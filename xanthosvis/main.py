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

sns.set()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{"name": "viewport", "content": "width=device-width"}])
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

# in file to be uploaded by the user
# in_file = os.path.join(root_dir, 'input', 'q_km3peryear_pm_abcd_mrtm_watch_1971_2001.csv.zip')
# get a list of available years from file
#start_year_list = xvu.get_available_years(in_file)
# set start year
#start_year = start_year_list[0]


# Runoff Statistic for the Choropleth Map
acceptable_statistics = ['mean', 'median', 'min', 'max', 'standard deviation']

# Process years to extract from the input file
# list comprehension to create a target year list of strings
#target_years_list = xvu.get_target_years(start_year,  end_year)
# Generate data


# read in data provided by user
# df = xvu.prepare_data(in_file, target_years_list, df_ref)

# get data frame to use for plotting the choropleth map
#df_per_basin = xvu.data_per_basin(df, acceptable_statistics[0], target_years_list)

# create plot
#choro_plot = xvu.plot_choropleth(df_per_basin, basin_features)

# Generate time series plot
# # basin id will come from the click event
#basin_id = 168

# # data frame of values for the target basin
#dfx = xvu.data_per_year_basin(df, basin_id, target_years_list)  #
# # plot hydrograph
#hydro_plot = xvu.plot_hydrograph(dfx, basin_id)

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
            ]), width=4, style={'border': '1px solid'}),
            dbc.Col(
                [
                    dbc.Row(
                        dbc.Col(html.Div([
                            dcc.Graph(
                                id='choro'
                            )
                        ]), style={'border': '1px solid'})
                    ),
                    dbc.Row(
                        dbc.Col(html.Div([
                            dcc.Graph(
                                id='hydro'
                            )
                        ]), style={'border': '1px solid'})
                    )
                ],
                width=7,
                style={'border': '1px solid'}
            )
        ]
    ),
        dcc.Store(id="data_store", storage_type="memory")
]
)

# Callback to generate error message
# Also sets the data to be used
# If there is an error use default data else use uploaded data
@app.callback(
    [
        Output("data_store", "data"),
        Output("error-message", "children"),
        Output("start_year", "options"),
        # Output("through_year", "options"),
        # Output("start_year", "value"),
        # Output("through_year", "value"),
        # Output("choro", "figure")
    ],
    [Input("upload-data", "contents")], [State('upload-data', 'filename'), State('upload-data', 'last_modified')],
    prevent_initial_call=True
)
def update_data(contents, filename, filedate):

    error_status = False
    error_message = None
    target_years = []

    # Check if there is uploaded content
    if contents:
       # xanthos_data = pd.read_csv(contents[0], compression='infer')
        for content, name, date in zip(contents, filename, filedate):
            # the content needs to be split. It contains the type and the real content
            content_type, content_string = content.split(',')
            # Decode the base64 string
            content_decoded = base64.b64decode(content_string)
            # Use BytesIO to handle the decoded content
            zip_str = io.BytesIO(content_decoded)
            # Now you can use ZipFile to take the BytesIO output
            zip_file = ZipFile(zip_str, 'r')
            filename = zip_file.namelist()[0]
        with zip_file.open(filename) as csvfile:
            xanthos_data = pd.read_csv(csvfile, encoding='utf8', sep=",")
        #xanthos_data = pd.read_csv(zip_file, compression='infer')
       # content_type, content_string = xanthos_data.split(",")
       # decoded = base64.b64decode(content_string)
        df_per_basin = []
        # Try reading uploaded file
        # try:
        #     missing_columns = {
        #         "id"
        #     }.difference(xanthos_data.columns)
        #
        #     if missing_columns:
        #         error_message = html.Div(
        #             className="alert",
        #             children=["Missing columns: " + str(missing_columns)],
        #         )
        #         error_status = True
        #        # study_data = default_study_data
        #
        # # Data is invalid
        # except Exception as e:
        #     error_message = html.Div(
        #         className="alert",
        #         children=["That doesn't seem to be a valid csv file!"],
        #     )
        #     error_status = True
            #study_data = default_study_data

    # Update Dropdown
        options = []
        target_years = xvu.get_available_years(xanthos_data)
        target_years = [str(i) for i in target_years]
        xanthos_data.columns = xanthos_data.columns.astype(str)
        xanthos_data['id'] = numpy.arange(len(xanthos_data))
        df = xvu.prepare_data(xanthos_data, target_years, df_ref)
        df_per_basin = xvu.data_per_basin(df, acceptable_statistics[0], target_years)
        options = target_years
        options_list = [{'label': i, 'value': i} for i in options]
        start_year = options_list[0]
        through_year = options_list[len(options_list) - 1]
        fig = xvu.plot_choropleth(df_per_basin, basin_features)
        # if "test_article" in xanthos_data.columns:
        #     test_articles = xanthos_data.test_article.unique()
        #     for test_article in test_articles:
        #         for study in xanthos_data.study_id[
        #             xanthos_data.test_article == test_article
        #         ].unique():
        #             options.append(
        #                 {"label": f"{test_article} (study: {study})", "value": study}
        #             )
        # else:
        #     for study in xanthos_data.study_id.unique():
        #         options.append({"label": study, "value": study})

        #options.sort(key=lambda item: item["label"])
       # value = options[0]["value"] if options else None
        return error_status, error_message, options_list#, options_list, start_year, through_year, fig



@app.callback(
    Output('through_year', 'options'),
    [Input('start_year', 'value'), Input('start_year', 'options')], prevent_initial_call=True)
def set_through_year_list(value, options):
    print(value)
    if value is None:
        year_list = xvu.available_through_years(options, options[0]['value'])
    else:
        year_list = xvu.available_through_years(options, value)

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
    # # fig = px.choropleth(new_data,
    # #              geojson=basin_json, locations='basin_id', color='q')
    # data = [dict(type='choropleth',
    #              geojson=basin_features,
    #              locations=new_data['basin_id'],
    #              z=new_data['q'],
    #              colorscale='Viridis')]
    # # go.Choropleth(geojson=basin_json, locations=new_data['basin_id'], z=new_data['q'],
    # #                       colorscale="Viridis"))]
    # layout = dict(title='My Title')
    # # fig = go.Figure(
    # #     data=go.Choropleth(geojson=basin_json, locations=new_data['basin_id'], z=new_data['q'], colorscale="Viridis"))
    # # fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    # return {
    #     'data': data,
    #     'layout': layout
    # }
    fig = xvu.update_choropleth(new_data, geojson_basin=basin_json)
    return fig


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
