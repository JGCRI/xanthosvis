# -*- coding: utf-8 -*-
import base64
import io
import os

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import numpy
import pandas as pd
import seaborn as sns
from dash.dependencies import Input, Output, State
import plotly.express as px
import copy
from zipfile import ZipFile
import xanthosvis.util_functions as xvu
import math

sns.set()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{"name": "viewport", "content": "width=device-width"}], suppress_callback_exceptions=True)
server = app.server
root_dir = 'include/'

# Reference Files
# reference file to be included in the package data
gridcell_ref_file = os.path.join(root_dir, 'reference', 'xanthos_0p5deg_landcell_reference.csv')
# read in reference file to dataframe
df_ref = pd.read_csv(gridcell_ref_file)
# reference geojson file for basins
basin_json = os.path.join(root_dir, 'reference', 'gcam_basins.geojson')
basin_features = xvu.process_geojson(basin_json)

# Runoff Statistic for the Choropleth Map
acceptable_statistics = ['mean', 'median', 'min', 'max', 'standard deviation']

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

app.layout = html.Div(children=[
    html.Div(id="error-message"),
    dbc.Row(
        [
            dbc.Col(html.Div([
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                    # Allow multiple files to be uploaded
                    multiple=True
                ),
                html.Div(id='output-data-upload'),
                dcc.RangeSlider(
                    id="year_slider",
                    min=1960,
                    max=2017,
                    value=[1990, 2010],
                    className="dcc_control",
                ),
                dcc.Dropdown(
                    id='statistic',
                    options=[{'label': i, 'value': i} for i in acceptable_statistics],
                    value=acceptable_statistics[0], clearable=False
                ),
                dcc.Dropdown(
                    id='start_year',
                    options=[],
                    clearable=False
                ),
                dcc.Dropdown(
                    id='through_year',
                    options=[], clearable=False
                ),
                html.Button('View Data', id='submit_btn', n_clicks=0),
            ]), width=4, style={'border': '1px solid'}),
            dbc.Col(
                [
                    dbc.Row(
                        dbc.Col(html.Div([
                            dcc.Graph(
                                id='choro_graph',
                                figure=dict(
                                    data=[],
                                    layout={})
                            )
                        ]), style={'border': '1px solid'})
                    ),
                    dbc.Row(
                        dbc.Col(html.Div([
                            dcc.Graph(
                                id='hydro_graph'
                            )
                        ]), style={'border': '1px solid'})
                    )
                ],
                width=7,
                style={'border': '1px solid'}
            )
        ]
    )
]
)


@app.callback(Output("choro_graph", "figure"),
              [Input("submit_btn", 'n_clicks')], [State("upload-data", "contents"), State("upload-data", "filename"),
                                                  State("upload-data", "last_modified"),
                                                  State("start_year", "value"), State("through_year", "value"), State("statistic", "value")],
              prevent_initial_call=True)
def update_choro(click, contents, filename, filedate, start, end, statistic):
    if contents:
        xanthos_data = xvu.process_file(contents, filename, filedate)
        year_list = xvu.get_target_years(start, end)
        df = xvu.prepare_data(xanthos_data, year_list, df_ref)
        df_per_basin = xvu.data_per_basin(df, statistic, year_list)

        data = [dict(type='choropleth',
                         geojson=basin_features,
                         locations=df_per_basin['basin_id'],
                         z=df_per_basin['q'],
                         colorscale='Viridis')]

        layout = dict(title='My Title')
        return {
                'data': data,
                'layout': layout
            }
    else:
        data = []

        layout = {}
        return {
                'data': data,
                'layout': layout
            }


# Callback to generate error message
# Also sets the data to be used
# If there is an error use default data else use uploaded data

@app.callback(
    [Output("start_year", "options"),  Output("start_year", "value")],
    [Input("upload-data", "contents")], [State('upload-data', 'filename'), State('upload-data', 'last_modified')],
    prevent_initial_call=True
)
def update_options(contents, filename, filedate):
    error_status = False
    error_message = None
    target_years = []

    # Check if there is uploaded content
    if contents:
        target_years = xvu.process_input_years(contents, filename, filedate)
        return target_years,  target_years[0]['value']


@app.callback(
    [Output('through_year', 'options'), Output('through_year', 'value')],
    [Input('start_year', 'value'), Input('start_year', 'options')], [State('through_year', 'value')], prevent_initial_call=True)
def set_through_year_list(value, options, current_value):
    print(value)
    if current_value is None:
        year_list = xvu.available_through_years(options, options[0]['value'])
        new_value = options[len(options)-1]['value']
    else:
        year_list = xvu.available_through_years(options, value)
        new_value = current_value

    return year_list, new_value


@app.callback(
    Output('hydro_graph', 'figure'),
    [Input('choro_graph', 'clickData')],
    [State('start_year', 'value'),
     State('through_year', 'value'),
     State("upload-data", "contents"), State('upload-data', 'filename'), State('upload-data', 'last_modified')], prevent_initial_call=True
)
def update_hydro(click_data, start, end, contents, filename, filedate):
    if click_data is None:
        return
    else:
        points = click_data['points']
        location = points[0]['location']
        years = xvu.get_target_years(start, end)
        max_basin_row = xvu.hydro_basin_lookup(location, df_ref)
        file_data = xvu.process_file(contents, filename, filedate, max_basin_row)
        processed_data = xvu.prepare_data(file_data, years, df_ref)
        hydro_data = xvu.data_per_year_basin(processed_data, location, years)
       # new_data = xvu.data_per_year_basin(df, location, years)
        return xvu.plot_hydrograph(hydro_data, location)


if __name__ == '__main__':
    app.run_server(debug=True)
