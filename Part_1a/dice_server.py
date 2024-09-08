# dice_server.py
# JMA 1 Sept 2024
#
### An interactive simulation of a Kelly sequential investment process
import os, sys
from pathlib import Path
import numpy as np
import pandas as pd
from flask import Flask, render_template, request

from bokeh.embed import components
from bokeh.layouts import layout, column
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, CustomJS, Button, Range1d, RangeSlider

from numpy.random import default_rng
rng = default_rng(seed=101)

INITIAL_WEALTH = 1E6
SIMULATION_COUNT = 10                     # Number of simulated trajectories
WIN_P = 0.6                               # Prob a wager will win
NUM_PERIODS = 10                          # Repetitions of the wager. 
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
    fraction_at_risk = kelly_rule(win_p_estimate) * plus_minus * rng.uniform(-EPS, EPS)
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

def plot_simulations(x,y):
    ''
    p= figure(
    title= f"Current Trials for P(win)= {WIN_P:.3} ",
    width = 700, height = 400, 
    background_fill_color="#fafafa",
    x_axis_label = 'Trials',
    y_axis_label = 'Accumulated wealth')
    # p.x_range = Range1d()
    # p.y_range = Range1d(0, max(y[NUM_PERIODS-1,:]))
    for k in range(SIMULATION_COUNT):
        w_df = pd.DataFrame({'y': y[:,k], 'x': x[:,k]})
        sim_src = ColumnDataSource(w_df)
        p.step(x='x', y='y', source=sim_src, line_alpha=0.4, line_color='grey')
    return(p)


def create_bokeh_plot():
    # Create a figure
    trajectories = figure(title="Wealth over Time ",x_axis_label='Trial', y_axis_label='Wealth')


    range_slider = RangeSlider(start=0, end=10, value=(1,9), step=.1, title="Stuff")
    range_slider.js_on_change("value", CustomJS(code="""
    console.log('range_slider: value=' + this.value, this.toString())                                           
    """))
    a_press = Button(label='Place amount at risk.', css_classes=[])
    slider_plot_layout = layout(column(trajectories, a_press, range_slider))

    # Return the plot components for embedding
    script, div = components(slider_plot_layout)
    # render_template uses jinja2 templating
    return render_template('./index.html', script=script, div=div)


app = Flask(__name__)

@app.route('/')
def index():
    html_component = create_bokeh_plot()
    return html_component

### MAIN ###

if __name__ == "__main__":
    # app.run(port = 8080)   # The mac uses port 5000 for airplay, so change the default port

    x,y = run_simulations()
    p= plot_simulations(x,y)
    show(p)
    print(pd.DataFrame(x).describe())