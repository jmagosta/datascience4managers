# c_server/main.py 
#
# An interactive Bokeh webpage to run a sequential investment game 
# and compare it to a set of Kelly-strategy trajectories. 
# Derived from c_server_es.py
#
# To Run:
# Part1a/ $ bokeh serve --show c_server --port=8090

import csv, os, sys
from pathlib import Path
import random
import numpy as np
import pandas as pd

from bokeh.events import ButtonClick, DocumentEvent
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, CustomJS, Button, Div, Range1d, Slider
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure, curdoc

# create a plot and style its properties
from numpy.random import default_rng
rng = default_rng(seed=142)

### Constants
INITIAL_WEALTH = 1E6
DEFAULT_AT_RISK = 0.5
SIMULATION_COUNT = 10                     # Number of simulated trajectories
WIN_P = 0.55                              # Prob a wager will win
NUM_PERIODS = 12                          # Repetitions of the wager. 
PKL_FILENAME = f'trajectories_{NUM_PERIODS}_by_{SIMULATION_COUNT}.pkl'
LOG_FILE = f'dice_{WIN_P}.csv'
EPS = 1E-1

### The simulation 
def kelly_rule(p):
    'The fraction to bet for an assumed win probability'
    # This works as a vectorized function 
    return ((2*p - 1) * (p > 0.5))

def investment_process(true_win_p = WIN_P, rounds=NUM_PERIODS-1):
    'A sequence of 1s and 0s, with win == 1, loss = 0. For the true win stochastic process.'
    return rng.binomial(1, true_win_p, rounds)

def wealth_trajectory(win_p_estimate):
    """
    Use the estimated win probability update as the bet fraction, using the Kelly rule
    to run a simulation for comparison with the player's trajectory.
    """
    wins = investment_process(win_p_estimate)
    periods = len(wins)
    # convert the stochastic series to -1, 1
    plus_minus = (2*wins-1) 
    # kelly strategy plus some jitter.
    fraction_at_risk = kelly_rule(win_p_estimate) * plus_minus
    # print(sum(fraction_at_risk))
    # Compute both wealth update and randomized update time
    w_x = np.zeros((NUM_PERIODS))
    w_y = np.zeros((NUM_PERIODS))
    
    w_y[0] = INITIAL_WEALTH
    #  Start at 0
    for period in range(1, NUM_PERIODS):
        w_x[period] = period - 1 + rng.uniform(EPS, 1-EPS)
        w_y[period] = w_y[period-1]* (1 + fraction_at_risk[period-1])

    return w_x, w_y

def run_simulations():
    trajectories_x = np.empty((NUM_PERIODS, SIMULATION_COUNT))
    trajectories_y = np.empty((NUM_PERIODS, SIMULATION_COUNT))
    for k in range(SIMULATION_COUNT):
        trajectories_x[:, k], trajectories_y[:, k] = wealth_trajectory(WIN_P)
    return trajectories_x, trajectories_y

# Track the user investment path; the trajectory
def chosen_trajectory(invest_fraction, past_trajectory, win_or_lose):
    'Compute the next increment of the investors wealth and append to past_trajectory.'
    delta_fraction = invest_fraction * (2 * win_or_lose -1)
    # print(f'\t {win_or_lose}, {delta_fraction}')
    # 
    past_trajectory['f'].append(invest_fraction)
    past_trajectory['t'].append(past_trajectory['t'][-1] +1)  # 
    past_trajectory['b'].append(int(delta_fraction * past_trajectory['w'][-1]))               # the bet result, either + or - 
    past_trajectory['w'].append(int(past_trajectory['w'][-1] * (1 + delta_fraction)))
    print('trajectory: ', past_trajectory)
    return past_trajectory

### IO ########

def create_log():
    with open(LOG_FILE, 'w', newline='') as fd:
        writer = csv.writer(fd)
        writer.writerow([f'trial_{WIN_P}', 'invest_fraction', 'bet', 'wealth'])
    return None

def append_log(bet, invest_fraction, past_trajectory):
    trial = past_trajectory['t'][-1]
    bet = past_trajectory['b'][-1]
    wealth = past_trajectory['w'][-1]
    with open(LOG_FILE, 'a', newline='') as fd:
        writer = csv.writer(fd)
        writer.writerow([trial, invest_fraction, bet, wealth])
    return None

### Display #####


def plot_simulations(past_trajectory, x,y, cycle):
    ''
    # global investment_cycle
    p= figure(
    title= f"Current Trials for P(win)= {WIN_P:.3} ",
    width = 700, height = 400, 
    background_fill_color="#fafafa",
    x_axis_label = 'Trials',
    y_axis_label = 'Accumulated wealth')
    p.x_range = Range1d(0, cycle+1)
    # p.y_range = Range1d(0, max(y[NUM_PERIODS-1,:]))
    p.xaxis.minor_tick_line_color = None
    p.xaxis.ticker = list(range(cycle+1))
    for k in range(SIMULATION_COUNT):
        w_df = pd.DataFrame({'y': y[:,k], 'x': x[:,k]})
        sim_src = ColumnDataSource(w_df)
        p.step(x='x', y='y', source=sim_src, line_alpha=0.4, line_color='grey')
    p.step(x=past_trajectory['t'], y=past_trajectory['w'], line_color='darkred', line_width=3)
    return p

### Callbacks 
def slider_handler(attr, old_v, new_v):
    'respond to changes in the slider value'
    global fraction_at_risk, value_at_risk, bet 
    fraction_at_risk = float(new_v)
    # Display the dollar amount at risk
    value_at_risk = int(fraction_at_risk *  past_trajectory['w'][-1])
    bet.data['frac'] = [fraction_at_risk]
    bet.data['value'] = [value_at_risk]
    # print('slider', bet.data['frac'], bet.data['value'])

# create a callback that adds a number in a random location
def button_callback():
    'Run the next investment cycle'
    global investment_cycle, past_trajectory, a_layout, bet
    investment_cycle +=1
    
    print(f"fraction @ Button {fraction_at_risk:.2}, {bet.data['value']}")
    win_p = rng.binomial(1, WIN_P, 1)[0]
    past_trajectory = chosen_trajectory(fraction_at_risk, past_trajectory, win_p)
    x,y = run_simulations()
    trajectories = plot_simulations(past_trajectory, x,y, investment_cycle)
    # Update the value at risk given the new wealth
    # NOTE is is already set in the slider callback?
    # value_at_risk = int(fraction_at_risk *  past_trajectory['w'][-1]) 
    bet.data['value'] = [value_at_risk]
    new_layout = controls(trajectories, d, a_press, fraction_slider)
    a_layout.children = new_layout.children
    print( f'Button {investment_cycle}: W=${past_trajectory['w'][-1]:.0f};{bet.data['value']}\n')
    append_log(bet, fraction_at_risk, past_trajectory )

# Called pretty much anytime something happens.
# This is needed to force a re-plot. 
def re_render(the_event):
    global a_layout, a_press, fraction_slider
    # print('render bet, frac, value: ', bet.data['frac'], bet.data['value'])
    pass

def controls(trajectories, d, a_press, fraction_slider):
    new_layout = column(trajectories, row(fraction_slider, d,  a_press))
    return new_layout

### MAIN #####################################################################

# Create widgets
# ColumnDataSource takes lists as dictionary values
# Make data available to widgets. 
bet = ColumnDataSource(data=dict(frac=[DEFAULT_AT_RISK], value=[DEFAULT_AT_RISK * INITIAL_WEALTH]))
d = Div(text=f"<font size='10'> investment: {bet.data['value'][0]} </font>")

fraction_slider = Slider(start=0, end=1.0, value=DEFAULT_AT_RISK, step=.01, title="Investment fraction", name='fraction_at_risk')
fraction_slider.js_on_change("value", CustomJS(args = dict(d=d, bets=bet), code=""" 
    var df = bets.data['value'][0];
    console.log('bets =', df);
    d.text=  `<font size='10'>Investment: ${df}</font>`                      
     """))                            
    #                          CustomJS(code="""
    # console.log('fraction_slider: value=' + this.value, this.toString())                                           

# NOTE slider handler updates globals fraction_at_risk and value_at_risk 
fraction_slider.on_change("value", slider_handler)

# the callback object cb_obj and callback data cb_data are available in each JS callback. 
# Additionally, when using args callback attribute 
# you can pass arbitrary number of additional objects
# bets.js_on_change("data", CustomJS(args=dict(d=d), "d.text = `<font size='40'>Value: ${cb_obj.data['value'][0]}`;</font>"))
# bets.js_on_change("value", CustomJS(args=dict(bets=bets),code= "console.log('bets ='  + bets"))
                                 
# def update_var():
#     ''
#     global bets
#     bets.data['value'][0] = [value_at_risk]

# bets.on_change('data', update_var)

# add a text renderer to the plot (no data yet)
# r = p.text(x=[], y=[], text=[], text_color=[], text_font_size="26px",
#            text_baseline="middle", text_align="center")
# bets = r.data_source

# add a button widget and configure with the call back
a_press = Button(label="Update investment")
a_press.button_type ='danger'
a_press.on_event('button_click', button_callback)
a_press.js_on_click(CustomJS(args = dict(d=d, bets=bet), code=""" 
    var df = bets.data['value'][0];
    console.log('bets =', df);
    d.text=  `<font size='10'>Bnvestment: ${df}</font>`                      
     """))  

### starting values
investment_cycle = 1
fraction_at_risk = DEFAULT_AT_RISK
value_at_risk = int(INITIAL_WEALTH * DEFAULT_AT_RISK)

# init
create_log()
# History of investment, with the first period a zero investment, for 
# purposes of plotting.  
past_trajectory = dict(f=[DEFAULT_AT_RISK, DEFAULT_AT_RISK] ,t=[0, investment_cycle], b=[0, value_at_risk], w=[INITIAL_WEALTH, INITIAL_WEALTH])
append_log(bet, fraction_at_risk, past_trajectory )

# past_trajectory = chosen_trajectory(bet.data['frac'][0], past_trajectory, rng.binomial(1, WIN_P,1)[0])
x,y = run_simulations()
trajectory_plot = plot_simulations(past_trajectory, x,y, investment_cycle)

### Event handling 
curdoc().on_change(re_render)
# curdoc().js_on_event(DocumentEvent, CustomJS(code='console.log("JS:DocumentEvent")'))

# put the button and plot in a layout and add to the document
a_layout = controls(trajectory_plot, d, a_press, fraction_slider)
curdoc().add_root(a_layout)