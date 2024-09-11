# c_server_es.py
#
# To Run:
# $ bokeh serve --show c_server_es.py --port=8090

import os, sys
from pathlib import Path
import random
import numpy as np
import pandas as pd

from bokeh.events import ButtonClick, DocumentEvent
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, CustomJS, Button, Div, Range1d, Slider
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure, curdoc

# create a plot and style its properties
from numpy.random import default_rng
rng = default_rng(seed=142)

INITIAL_WEALTH = 1E6
DEFAULT_AT_RISK = 0.5
SIMULATION_COUNT = 10                     # Number of simulated trajectories
WIN_P = 0.55                               # Prob a wager will win
NUM_PERIODS = 12                          # Repetitions of the wager. 
PKL_FILENAME = f'trajectories_{NUM_PERIODS}_by_{SIMULATION_COUNT}.pkl'
EPS = 1E-1

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

def chosen_trajectory(invest_fraction, past_trajectory, win_or_lose):
    'Compute the next increment of the investors wealth.'
    delta_fraction = invest_fraction * (2 * win_or_lose -1)
    # print(f'\t {win_or_lose}, {delta_fraction}')
    # x
    past_trajectory['x'].append(past_trajectory['x'][-1] +1)
    past_trajectory['y'].append(past_trajectory['y'][-1] * (1 + delta_fraction))
    return past_trajectory


def plot_simulations(past_trajectory, x,y, cycle):
    ''
    # global investment_cycle
    p= figure(
    title= f"Current Trials for P(win)= {WIN_P:.3} ",
    width = 700, height = 400, 
    background_fill_color="#fafafa",
    x_axis_label = 'Trials',
    y_axis_label = 'Accumulated wealth')
    p.x_range = Range1d(0, cycle)
    # p.y_range = Range1d(0, max(y[NUM_PERIODS-1,:]))
    p.xaxis.minor_tick_line_color = None
    p.xaxis.ticker = list(range(cycle+1))
    for k in range(SIMULATION_COUNT):
        w_df = pd.DataFrame({'y': y[:,k], 'x': x[:,k]})
        sim_src = ColumnDataSource(w_df)
        p.step(x='x', y='y', source=sim_src, line_alpha=0.4, line_color='grey')
    p.step(x=past_trajectory['x'], y=past_trajectory['y'], line_color='darkred', line_width=3)
    return(p)

### Callbacks 
def slider_handler(attr, old_v, new_v):
    'respond to changes in the slider value'
    global fraction_at_risk, value_at_risk, ds
    fraction_at_risk = float(new_v)
    # Display the dollar amount at risk
    value_at_risk = int(fraction_at_risk *  past_trajectory['y'][-1])
    ds.data['value'] = [value_at_risk]
    print('ds', ds.data['value'])
    # print(f'value_at_risk {value_at_risk}')

# create a callback that adds a number in a random location
def button_callback():
    'Run the next investment cycle'
    global investment_cycle, past_trajectory, a_layout, ds
    investment_cycle +=1
    
    print(f"fraction @ Button {fraction_at_risk:.2}, {ds.data['value']}\n")
    past_trajectory = chosen_trajectory(fraction_at_risk, past_trajectory, rng.binomial(1, WIN_P, 1)[0])
    x,y = run_simulations()
    trajectories = plot_simulations(past_trajectory, x,y, investment_cycle)
    # Update the value at risk given the new wealth
    value_at_risk = int(fraction_at_risk *  past_trajectory['y'][-1]) 
    ds.data['value'] = [value_at_risk]
    new_layout = column(trajectories, d, a_press, fraction_slider)
    a_layout.children = new_layout.children
    print( f'{investment_cycle}: W=${past_trajectory['y'][-1]:.0f}')

# Called pretty much anytime something happens.
# This is needed to force a re-plot. 
def re_render(the_event):
    global a_layout, a_press, fraction_slider
    print('render ds', ds.data['value'])
    pass

    

### MAIN #####################################################################

investment_cycle = 1
fraction_at_risk = 0.0
value_at_risk = int(INITIAL_WEALTH * DEFAULT_AT_RISK)
# History of investment
past_trajectory = dict(x=[0], y=[INITIAL_WEALTH])

# ColumnDataSource takes lists as dictionary values
ds = ColumnDataSource(data=dict(frac=[fraction_at_risk], value=[value_at_risk]))

d = Div(text=f"<font size='10'> investment: {ds.data['value'][0]} </font>")

    # Create widgets
fraction_slider = Slider(start=0, end=1.0, value=DEFAULT_AT_RISK, step=.01, title="Investment fraction", name='fraction_at_risk')
fraction_slider.js_on_change("value", CustomJS(args = dict(d=d, ds=ds), code=""" 
    var df = ds.data['value'][0];
    console.log('ds =', df);
    d.text=  `<font size='10'>Investment: ${df}</font>`                      
     """))                            
    #                          CustomJS(code="""
    # console.log('fraction_slider: value=' + this.value, this.toString())                                           

fraction_slider.on_change("value", slider_handler)



# the callback object cb_obj and callback data cb_data are available in each JS callback. 
# Additionally, when using args callback attribute 
# you can pass arbitrary number of additional objects
# ds.js_on_change("data", CustomJS(args=dict(d=d), "d.text = `<font size='40'>Value: ${cb_obj.data['value'][0]}`;</font>"))
# ds.js_on_change("value", CustomJS(args=dict(ds=ds),code= "console.log('ds ='  + ds"))
                                 

# def update_var():
#     ''
#     global ds
#     ds.data['value'][0] = [value_at_risk]

# ds.on_change('data', update_var)

# add a text renderer to the plot (no data yet)
# r = p.text(x=[], y=[], text=[], text_color=[], text_font_size="26px",
#            text_baseline="middle", text_align="center")
# ds = r.data_source

# add a button widget and configure with the call back
a_press = Button(label="Update investment")
a_press.button_type ='danger'
a_press.on_event('button_click', button_callback)
a_press.js_on_click(CustomJS(args = dict(d=d, ds=ds), code=""" 
    var df = ds.data['value'][0];
    console.log('ds =', df);
    d.text=  `<font size='10'>Bnvestment: ${df}</font>`                      
     """))  

past_trajectory = chosen_trajectory(2*WIN_P-1, past_trajectory, rng.binomial(1, WIN_P,1)[0])
x,y = run_simulations()
trajectories = plot_simulations(past_trajectory, x,y, investment_cycle)

curdoc().on_change(re_render)
# curdoc().js_on_event(DocumentEvent, CustomJS(code='console.log("JS:DocumentEvent")'))

# put the button and plot in a layout and add to the document
a_layout = column(trajectories, d, a_press, fraction_slider)
curdoc().add_root(a_layout)