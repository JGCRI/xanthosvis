# -*- coding: utf-8 -*-
import base64
import io
import os

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import seaborn as sns
from dash.dependencies import Input, Output
import plotly.express as px
import copy
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
target_years_list = xvu.get_target_years(start_year,
                                         end_year)  # [str(i) for i in range(start_year, end_year + 1)]  # range(start_year, max(through_years_list), 1)]
# Generate data


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
        ],
        dcc.Store(id="data_store", storage_type="memory"),
    )
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
    ],
    [Input("upload-data", "contents")],
)
def update_data(contents):

    error_status = False
    error_message = None
   # study_data = default_study_data

    # Check if there is uploaded content
    if contents:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)

        # Try reading uploaded file
        try:
            study_data = pd.read_csv(io.StringIO(decoded.decode("utf-8")),  compression='infer', nrows=0)

            missing_columns = {
                "id"
            }.difference(study_data.columns)

            if missing_columns:
                error_message = html.Div(
                    className="alert",
                    children=["Missing columns: " + str(missing_columns)],
                )
                error_status = True
               # study_data = default_study_data

        # Data is invalid
        except Exception as e:
            error_message = html.Div(
                className="alert",
                children=["That doesn't seem to be a valid csv file!"],
            )
            error_status = True
            #study_data = default_study_data

    # Update Dropdown
    options = []
    if "test_article" in study_data.columns:
        test_articles = study_data.test_article.unique()
        for test_article in test_articles:
            for study in study_data.study_id[
                study_data.test_article == test_article
            ].unique():
                options.append(
                    {"label": f"{test_article} (study: {study})", "value": study}
                )
    else:
        for study in study_data.study_id.unique():
            options.append({"label": study, "value": study})

    options.sort(key=lambda item: item["label"])
    value = options[0]["value"] if options else None

    return error_status, error_message, options, value



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
