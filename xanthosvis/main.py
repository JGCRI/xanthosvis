# -*- coding: utf-8 -*-
import os
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import pandas as pd
from sklearn.linear_model import LinearRegression
import plotly.express as px
import math
from dash.dependencies import Input, Output, State
from datetime import datetime
import base64
import datetime
import io
import dash_table
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()
import xanthosvis.util_functions as xvu
import ipywidgets as widgets
import json

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

root_dir = '/Users/d3y010/projects/evanoff/xanthosvis/data'

# reference file to be included in the package data
gridcell_ref_file = os.path.join(root_dir, 'reference', 'xanthos_0p5deg_landcell_reference.csv')

# reference geojson file for basins
basin_json = os.path.join(root_dir, 'reference', 'gcam_basins.geojson')

# in file to be uploaded by the user
in_file = os.path.join(root_dir, 'input', 'q_km3peryear_pm_abcd_mrtm_watch_1971_2001.csv.zip')
# get a list of available years from file
available_year_list = xvu.get_available_years(in_file)

# get start year from user input
start_year = widgets.Dropdown(
    options=available_year_list,
    value=min(available_year_list),
    description='Start Year:',
    disabled=False,
)

display(start_year)
print(start_year.value)

# get a list of available through years
through_years_list = xvu.available_through_years(available_year_list, start_year.value)

# get through year from user input
through_year = widgets.Dropdown(
    options=through_years_list,
    value=max(through_years_list),
    description='Through Year:',
    disabled=False,
)

display(through_year)
print(through_year.value)

# Runoff Statistic for the Choropleth Map
acceptable_statistics = ['mean', 'median', 'min', 'max', 'standard deviation']

# get through year from user input
statistic = widgets.Dropdown(
    options=acceptable_statistics,
    description='Runoff statistic:',
    disabled=False,
)

display(statistic)
print(statistic.value)

# Process years to extract from the input file
# list comprehension to create a target year list of strings
target_years_list = [str(i) for i in range(start_year.value, through_year.value + 1, 1)]
#Generate data
# read in reference file to dataframe
df_ref = pd.read_csv(gridcell_ref_file)

# read in data provided by user
df = xvu.prepare_data(in_file, target_years_list, df_ref)

# get data frame to use for plotting the choropleth map
df_per_basin = xvu.data_per_basin(df, statistic.value, target_years_list)

# create plot
xvu.plot_choropleth(df_per_basin, basin_json)

# Generate time series plot
# # basin id will come from the click event
basin_id = 168

# # data frame of values for the target basin
dfx = xvu.data_per_year_basin(df, basin_id)#
# # plot hydrograph
xvu.plot_hydrograph(dfx, basin_id)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

df = pd.read_csv('include/Diagnostics_Runoff_Basin_Scale_km3peryr.csv')

x = df['xanthos'].values.reshape(-1, 1)
y = df['VIC_1971-2000'].values.reshape(-1, 1)
model = LinearRegression().fit(x, y)
r_sq = model.score(x, y)

fig = px.scatter(df, x="xanthos", y="VIC_1971-2000", trendline="ols")
fig.update_layout(
    title={'text': "Xanthos to VIC Runoff: R=" + str(round(math.sqrt(r_sq), 6)), 'y': 0.9, 'x': 0.5,
           'xanchor': 'center', 'yanchor': 'top'},
    xaxis_title="Xanthos Runoff (km\N{SUPERSCRIPT THREE}/yr)",
    yaxis_title="VIC Runoff (km\N{SUPERSCRIPT THREE}/yr)",
    # height:400,
    # margin: {'l': 10, 'b': 20, 't': 0, 'r': 0}
    # font=dict(
    #     family="Courier New, monospace",
    #     size=18,
    #     color="#7f7f7f"
    # ) 'height': 400,
    #                                     'margin': {'l': 10, 'b': 20, 't': 0, 'r': 0}
)

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
            ]), width=6, style={'border': '1px solid'}),
            dbc.Col(
                [
                    dbc.Row(
                        dbc.Col(html.Div('Nested Row1-Col2-Row1'), style={'border': '1px solid'})
                    ),
                    dbc.Row(
                        dbc.Col(html.Div([
                            dcc.Graph(
                                id='life-exp-vs-gdp',
                                figure=fig
                            )
                        ]), style={'border': '1px solid'})
                    )
                ],
                width=6,
                style={'border': '1px solid'}
            )
        ]
    )
]
)


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df2 = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df2 = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),

        dash_table.DataTable(
            data=df2.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df2.columns]
        ),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])


@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children


if __name__ == '__main__':
    app.run_server(debug=True)

# def dump_this():
#     return 0
