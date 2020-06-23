# -*- coding: utf-8 -*-
import os

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import seaborn as sns
from dash.dependencies import Input, Output
import plotly.express as px

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
start_year_list = xvu.get_available_years(in_file)
# set start year
start_year = start_year_list[0]
end_year = start_year_list[len(start_year_list) - 1]

# get a list of available through years
through_years_list = start_year_list  # xvu.available_through_years(start_year_list, start_year)

# Runoff Statistic for the Choropleth Map
acceptable_statistics = ['mean', 'median', 'min', 'max', 'standard deviation']

# Process years to extract from the input file
# list comprehension to create a target year list of strings
target_years_list = xvu.get_target_years(start_year, end_year)  # [str(i) for i in range(start_year, end_year + 1)]  # range(start_year, max(through_years_list), 1)]
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
dfx = xvu.data_per_year_basin(df, basin_id, target_years_list)  #
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
                    options=[{'label': i, 'value': i} for i in start_year_list],
                    value=start_year_list[0], clearable=False
                ),
                dcc.Dropdown(
                    id='through_year',
                    options=[{'label': i, 'value': i} for i in through_years_list],
                    value=start_year_list[len(start_year_list) - 1], clearable=False
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
    Output('through_year', 'options'),
    [Input('start_year', 'value')])
def set_through_year_list(value):
    print(value)
    year_list = xvu.available_through_years(start_year_list, value)
    return year_list


@app.callback(
    Output('choro', 'figure'),
    [Input('start_year', 'value'),
     Input('through_year', 'value'),
     Input('statistic', 'value')], prevent_initial_call=True)
def update_choro(start, end, stat):
    print(start, end)
    years = xvu.get_target_years(start, end)
    new_data = xvu.data_per_basin(df, stat, years)
    # fig = px.choropleth(new_data,
    #              geojson=basin_json, locations='basin_id', color='q')
    data = [dict(type='choropleth',
                 geojson=basin_features,
                 locations=new_data['basin_id'],
                 z=new_data['q'],
                 colorscale='Viridis')]
    # go.Choropleth(geojson=basin_json, locations=new_data['basin_id'], z=new_data['q'],
    #                       colorscale="Viridis"))]
    layout = dict(title='My Title')
    # fig = go.Figure(
    #     data=go.Choropleth(geojson=basin_json, locations=new_data['basin_id'], z=new_data['q'], colorscale="Viridis"))
    # fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return {
        'data': data,
        'layout': layout
    }


@app.callback(
    Output('hydro', 'figure'),
    [Input('choro', 'clickData'),
     Input('start_year', 'value'),
     Input('through_year', 'value')], prevent_initial_call=True)
def update_hydro(click_data, start, end):
    points = click_data['points']
    location = points[0]['location']
    years = xvu.get_target_years(start, end)
    new_data = xvu.data_per_year_basin(df, location, years)
    return xvu.plot_hydrograph(new_data, location)


if __name__ == '__main__':
    app.run_server(debug=True)

# def dump_this():
#     return 0
