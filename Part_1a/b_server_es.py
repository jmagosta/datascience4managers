# bokeh server example
# From https://gist.github.com/mrocklin/e014f11aab7eb3fd12d83a746d8c87df 
# JMA 8 Sept 2024
#
# To run
# $ bokeh serve b_server_es.py --port=8080

from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.plotting import curdoc, figure, ColumnDataSource, curdoc

# import random
from numpy.random import default_rng
rng = default_rng(seed=101)

def make_document(doc):
    source = ColumnDataSource({'x': [1,2], 'y': [2,3], 'color': []})

    def update():
        new = {'x': [rng.random()],
               'y': [rng.random()],
               'color': [rng.choice(['red', 'blue', 'green'])]}
        source.stream(new)

        print(source.data.values)

    # doc.add_periodic_callback(update, 100)

    fig = figure(title='Streaming Circle Plot!', sizing_mode='scale_width',
                 x_range=[0, 1], y_range=[0, 1])
    fig.circle(source=source, x='x', y='y', color='color', size=10)

    curdoc.title = "Now with live updating!"
    curdoc.add_root(fig)
    
apps = {'/': Application(FunctionHandler(make_document))}

server = Server(apps) # , port=80801)
server.start()