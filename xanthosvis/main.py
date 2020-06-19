# -*- coding: utf-8 -*-
import os

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import ipywidgets as widgets
import pandas as pd
import seaborn as sns
import json

import xanthosvis.util_functions as xvu

sns.set()

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

root_dir = 'include/'

# reference file to be included in the package data
gridcell_ref_file = os.path.join(root_dir, 'reference', 'xanthos_0p5deg_landcell_reference.csv')

# reference geojson file for basins
basin_json = os.path.join(root_dir, 'reference', 'gcam_basins.geojson')

# in file to be uploaded by the user
in_file = os.path.join(root_dir, 'input', 'q_km3peryear_pm_abcd_mrtm_watch_1971_2001.csv.zip')
# get a list of available years from file
available_year_list = xvu.get_available_years(in_file)
# set start year
start_year = available_year_list[0]

# get a list of available through years
through_years_list = xvu.available_through_years(available_year_list, start_year)

# Runoff Statistic for the Choropleth Map
acceptable_statistics = ['mean', 'median', 'min', 'max', 'standard deviation']

# Process years to extract from the input file
# list comprehension to create a target year list of strings
target_years_list = [str(i) for i in range(start_year,  max(through_years_list), 1)]
# Generate data
# read in reference file to dataframe
df_ref = pd.read_csv(gridcell_ref_file)

# read in data provided by user
df = xvu.prepare_data(in_file, target_years_list, df_ref)

# get data frame to use for plotting the choropleth map
df_per_basin = xvu.data_per_basin(df, acceptable_statistics[0], target_years_list)
basin_features = xvu.process_geojson(basin_json)

# create plot
choro_plot = xvu.plot_choropleth(df_per_basin, basin_features)

# Generate time series plot
# # basin id will come from the click event
basin_id = 168

# # data frame of values for the target basin
dfx = xvu.data_per_year_basin(df, basin_id)  #
# # plot hydrograph
hydro_plot = xvu.plot_hydrograph(dfx, basin_id)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

app.layout = html.Div([
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
                dcc.Dropdown(
                    id='statistic',
                    options=[{'label': i, 'value': i} for i in acceptable_statistics],
                    value=acceptable_statistics[0], clearable=False
                ),
                dcc.Dropdown(
                    id='start_year',
                    options=[{'label': i, 'value': i} for i in available_year_list],
                    value=available_year_list[0], clearable=False
                ),
                dcc.Dropdown(
                    id='through_year',
                    options=[{'label': i, 'value': i} for i in through_years_list],
                    value=available_year_list[len(available_year_list) - 1], clearable=False
                ),
            ]), width=4, style={'border': '1px solid'}),
            dbc.Col(
                [
                    dbc.Row(
                        dbc.Col(html.Div([
                            dcc.Graph(
                                id='choro',
                                figure=choro_plot
                            )
                        ]), style={'border': '1px solid'})
                    ),
                    dbc.Row(
                        dbc.Col(html.Div([
                            dcc.Graph(
                                id='hydro',
                                figure=hydro_plot
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


@app.callback(
    dash.dependencies.Output('through_year', 'options'),
    [dash.dependencies.Input('start_year', 'value')])
def set_through_year_list(value):
    print(value)
    return [{'label': i, 'value': i} for i in through_years_list if i >= value]


@app.callback(
    dash.dependencies.Output('choro', 'figure'),
    [dash.dependencies.Input('start_year', 'value'),
     dash.dependencies.Input('through_year', 'value'),
     dash.dependencies.Input('statistic', 'value')])
def update_choro(start, end, stat):
    print(start, end)
    new_data = xvu.data_per_basin(df, stat, target_years_list[start:end])
    return xvu.update_choropleth(new_data, choro_plot)


#
# @app.callback(dash.dependencies.Output('through_year'  'options'),
#     [dash.dependencies.Input('start_year', 'value')])
# def set_through_year(start_year):
#     return [{'label': i, 'value': i} for i in all_options[selected_country]]

# @app.callback(dash.dependencies.Output('choro', 'figure'),
#     [dash.dependencies.Input('start_year', 'value'),
#      dash.dependencies.Input('end_year', 'value')])
# def update_graph(start_year, end_year):
#     xvu.prepare_data(in_file, target_years_list, df_ref)
#     return {
#         'data': [dict(
#             x=dff[dff['Indicator Name'] == xaxis_column_name]['Value'],
#             y=dff[dff['Indicator Name'] == yaxis_column_name]['Value'],
#             text=dff[dff['Indicator Name'] == yaxis_column_name]['Country Name'],
#             customdata=dff[dff['Indicator Name'] == yaxis_column_name]['Country Name'],
#             mode='markers',
#             marker={
#                 'size': 15,
#                 'opacity': 0.5,
#                 'line': {'width': 0.5, 'color': 'white'}
#             }
#         )],
#         'layout': dict(
#             xaxis={
#                 'title': xaxis_column_name,
#                 'type': 'linear' if xaxis_type == 'Linear' else 'log'
#             },
#             yaxis={
#                 'title': yaxis_column_name,
#                 'type': 'linear' if yaxis_type == 'Linear' else 'log'
#             },
#             margin={'l': 40, 'b': 30, 't': 10, 'r': 0},
#             height=450,
#             hovermode='closest'
#         )
#     }


if __name__ == '__main__':
    app.run_server(debug=True)

# def dump_this():
#     return 0
