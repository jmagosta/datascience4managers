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
from bokeh.models import ColumnDataSource, CustomJS, Button, Range1d, RangeSlider
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure, curdoc

# create a plot and style its properties
from numpy.random import default_rng
rng = default_rng(seed=142)

INITIAL_WEALTH = 1E6
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
    print(sum(fraction_at_risk))
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
    fraction_at_risk = invest_fraction * (2 * win_or_lose -1)
    print(f'\t {win_or_lose}, {fraction_at_risk}')
    # x
    past_trajectory['x'].append(past_trajectory['x'][-1] +1)
    past_trajectory['y'].append(past_trajectory['y'][-1] * (1 + fraction_at_risk))
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

# create a callback that adds a number in a random location
def button_callback():
    'Run the next investment cycle'
    global investment_cycle, past_trajectory, a_layout

    investment_cycle +=1
    past_trajectory = chosen_trajectory(2*WIN_P-1, past_trajectory, rng.binomial(1, WIN_P, 1)[0])
    x,y = run_simulations()
    trajectories = plot_simulations(past_trajectory, x,y, investment_cycle)
    new_layout = column(trajectories, a_press, range_slider)
    a_layout.children = new_layout.children
    print( f'{investment_cycle}: W=${past_trajectory['y'][-1]:.0f}')

def re_render(the_event):
    global a_layout, a_press, range_slider
    pass
    # print(f're_render {investment_cycle}, {the_event}')

### MAIN ###

investment_cycle = 1
past_trajectory = dict(x=[0], y=[INITIAL_WEALTH])

    # Create widgets
range_slider = RangeSlider(start=0, end=10, value=(1,9), step=.1, title="Stuff")
range_slider.js_on_change("value", CustomJS(code="""
    console.log('range_slider: value=' + this.value, this.toString())                                           
    """))

# add a text renderer to the plot (no data yet)
# r = p.text(x=[], y=[], text=[], text_color=[], text_font_size="26px",
#            text_baseline="middle", text_align="center")
# ds = r.data_source

# add a button widget and configure with the call back
a_press = Button(label="Update investment")
a_press.button_type ='danger'
a_press.on_event('button_click', button_callback)

past_trajectory = chosen_trajectory(2*WIN_P-1, past_trajectory, rng.binomial(1, WIN_P,1)[0])
x,y = run_simulations()
trajectories = plot_simulations(past_trajectory, x,y, investment_cycle)

curdoc().on_change(re_render)
# curdoc().js_on_event(DocumentEvent, CustomJS(code='console.log("JS:DocumentEvent")'))

# put the button and plot in a layout and add to the document
a_layout = column(trajectories, a_press, range_slider)
curdoc().add_root(a_layout)