# dice_server.py
# JMA 1 Sept 2024
#
### An interactive simulation of a Kelly sequential investment process
import os, sys
from flask import Flask, render_template, request

from bokeh.embed import components
from bokeh.plotting import figure, output_file, show

def create_bokeh_plot():
    # Create a figure
    p = figure(title="Bokeh Plot", x_axis_label='X-Axis', y_axis_label='Y-Axis')

    # Add data to the plot (replace with your data)
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 5, 3, 1]
    p.line(x, y, line_width=2)

    # Return the plot components for embedding
    script, div = components(p)
    return render_template('./index.html', script=script, div=div)


app = Flask(__name__)

@app.route('/')
def index():
    html_component = create_bokeh_plot()
    return html_component

### MAIN ###

if __name__ == "__main__":
    # wd = os.getcwd()
    # print(f'wd {wd}:  {os.listdir()}')
    app.run(port = 8080)   # The mac uses port 5000 for airplay, so change the default port

