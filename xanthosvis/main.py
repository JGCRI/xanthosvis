# -*- coding: utf-8 -*-
import os
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import seaborn as sns
from dash.dependencies import Input, Output, State
import xanthosvis.util_functions as xvu
import plotly.graph_objs as go
import plotly.express as px

sns.set()

group_colors = {"control": "light blue", "reference": "red"}

app = dash.Dash(__name__, external_stylesheets=['assets/base.css', 'assets/custom.css'],
                meta_tags=[{"name": "viewport", "content": "width=device-width"}], suppress_callback_exceptions=True)
server = app.server
root_dir = 'include/'

# Access Token for Mapbox
mapbox_token = open("include/mapbox-token").read()

# --- Reference Files
# reference file to be included in the package data
gridcell_ref_file = os.path.join(root_dir, 'reference', 'xanthos_0p5deg_landcell_reference.csv')
# read in reference file to dataframe
df_ref = pd.read_csv(gridcell_ref_file)
# reference geojson file for basins
basin_json = os.path.join(root_dir, 'reference', 'gcam_basins.geojson')
basin_features = xvu.process_geojson(basin_json)

# Runoff Statistic for the Choropleth Map
acceptable_statistics = [{'label': 'Mean', 'value': 'mean'}, {'label': 'Median', 'value': 'median'},
                         {'label': 'Min', 'value': 'min'}, {'label': 'Max', 'value': 'max'},
                         {'label': 'Standard Deviation', 'value': 'standard deviation'}]

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

app.layout = html.Div(
    children=[
        html.Div(id="error-message"),
        html.Div(
            className="study-browser-banner row",
            children=[
                html.H2(className="h2-title", children="Xanthos Data Visualization"),
                html.Div(
                    className="div-logo",
                    children=[
                        html.A([
                            html.Img(className="logo", src=app.get_asset_url("gcims_logo.svg")
                                     ),
                        ],
                            href="https://gcims.pnnl.gov/global-change-intersectoral-modeling-system", target="blank",
                        ),
                    ]),
                html.H2(className="h2-title-mobile", children="Xanthos Data Visualization"),
            ],
        ),
        # Body of the App
        html.Div(
            className="row app-body",
            children=[
                # User Controls
                html.Div(
                    className="four columns card",
                    children=[
                        html.Div(
                            className="bg-white user-control",
                            children=[
                                html.Div(
                                    className="padding-top-bot",
                                    children=[
                                        html.H6("Data Upload (File Types: .csv, zipped .csv)"),
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
                                                'textAlign': 'center'
                                            },
                                            # Allow multiple files to be uploaded
                                            multiple=True
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="padding-top-bot",
                                    children=[
                                        html.H6("Choose Statistic:"),
                                        dcc.Dropdown(
                                            id='statistic',
                                            options=[{'label': i['label'], 'value': i['value']} for i in
                                                     acceptable_statistics],
                                            value=acceptable_statistics[0]['value'], clearable=False
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="padding-top-bot",
                                    children=[
                                        html.H6("Choose Starting Year:"),
                                        dcc.Dropdown(
                                            id='start_year',
                                            options=[],
                                            clearable=False
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="padding-top-bot",
                                    children=[
                                        html.H6("Choose End Year:"),
                                        dcc.Dropdown(
                                            id='through_year',
                                            options=[], clearable=False
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="padding-top-bot",
                                    children=[
                                        html.Button('View Data', id='submit_btn', n_clicks=0),
                                    ],
                                ),
                                html.Div(
                                    className="padding-top-bot",
                                    children=[
                                        html.A(["Find Xanthos on GitHub"], href="https://github.com/JGCRI/xanthos",
                                               target="blank", className="a-xanthos-link")
                                    ]
                                ),
                            ],
                        )
                    ],
                ),
                # Graphs
                html.Div(
                    className="eight columns card-left",
                    children=[
                        html.Div(
                            className="bg-white",
                            children=[
                                dcc.Loading(
                                    id="loader",
                                    type="default",
                                    children=html.Div(id="loading-output",
                                                      style={
                                                          'z-index': '2',
                                                          'width': '100%',
                                                          'height': '100%',
                                                          'top': '100px',
                                                          'textAlign': 'center'
                                                      })
                                ),
                                # html.H5("Choro Plot"),
                                dcc.Graph(
                                    id='choro_graph',
                                    style={
                                        'z-index': '2'
                                    }
                                ),
                                # html.H5("Hydro Plot"),
                                dcc.Graph(
                                    id='hydro_graph'
                                )
                            ],
                        )
                    ],
                ),
            ],
        ),
    ]
)


# Callback to generate and load the choropleth graph when user clicks load data button
@app.callback([Output("choro_graph", "figure"), Output("error-message", "children"), Output("loader", "children")],
              [Input("submit_btn", 'n_clicks')],
              [State("upload-data", "contents"), State("upload-data", "filename"),
               State("upload-data", "last_modified"),
               State("start_year", "value"), State("through_year", "value"),
               State("statistic", "value")],
              prevent_initial_call=True)
def update_choro(click, contents, filename, filedate, start, end, statistic):
    error_message = None
    if contents:
        if start > end:
            error_message = html.Div(
                className="alert",
                children=["Invalid Years: Please choose a start year that is less than end year."],
            )
            return {
                       'data': [],
                       'layout': {}
                   }, error_message

        year_list = xvu.get_target_years(start, end)
        data = xvu.process_file(contents, filename, filedate, years=year_list)
        xanthos_data = data[0]
        units = data[1]
        df = xvu.prepare_data(xanthos_data, df_ref)
        df_per_basin = xvu.data_per_basin(df, statistic, year_list, df_ref)
        df_per_basin['Runoff (km³)'] = round(df_per_basin['q'], 2)
        # df_per_basin['Runoff (km³)'] = pd.cut(df_per_basin['Runoff (km³)'], range(0, max(df_per_basin['Runoff (km³)']),
        #                                                                           10), right=False, )
        fig = px.choropleth_mapbox(df_per_basin, geojson=basin_features, locations='basin_id',
                                   featureidkey='properties.basin_id', hover_name='basin_name',
                                   color='Runoff (km³)', color_continuous_scale="Viridis", zoom=0, opacity=0.7)
        fig.update_layout(
            title={
                'text': f"<b>Runoff by Basin {start} - {end}</b>",
                'y': 0.94,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(
                    family='Roboto',
                    size=20
                ),
            },
            xaxis_title="Lon",
            yaxis_title="Lat",
            margin=go.layout.Margin(
                l=30,  # left margin
                r=10,  # right margin
                b=10,  # bottom margin
                t=60  # top margin
            ),
        )
        fig.update_layout(mapbox_style="mapbox://styles/jevanoff/ckckto2j900k01iomsh1f8i20",
                          mapbox_accesstoken=mapbox_token)

        return fig, None, None

    else:
        data = []

        layout = {}
        return {
                   'data': data,
                   'layout': layout
               }, None, None


# Callback to set start year options when file is uploaded
# Also sets the data to be used
@app.callback(
    [Output("start_year", "options"), Output("start_year", "value"), Output("upload-data", "children")],
    [Input("upload-data", "contents")], [State('upload-data', 'filename'), State('upload-data', 'last_modified')],
    prevent_initial_call=True
)
def update_options(contents, filename, filedate):
    # Check if there is uploaded content
    if contents:
        target_years = xvu.process_input_years(contents, filename, filedate)
        name = filename[0]
        new_text = html.Div(["Using file " + name[:25] + '...' if (len(name) > 25) else "Using file " + name])
        return target_years, target_years[0]['value'], new_text


# Callback to set through year options when start year changes
@app.callback(
    [Output('through_year', 'options'), Output('through_year', 'value')],
    [Input('start_year', 'value'), Input('start_year', 'options')], [State('through_year', 'value')],
    prevent_initial_call=True)
def set_through_year_list(value, options, current_value):
    print(value)
    if current_value is None:
        year_list = xvu.available_through_years(options, options[0]['value'])
        new_value = options[len(options) - 1]['value']
    else:
        year_list = xvu.available_through_years(options, value)
        new_value = current_value

    return year_list, new_value


# Callback to load the per basin hydro graph when user clicks on choropleth graph
@app.callback(
    Output('hydro_graph', 'figure'),
    [Input('choro_graph', 'clickData'), Input("submit_btn", 'n_clicks')],
    [State('start_year', 'value'),
     State('through_year', 'value'),
     State("upload-data", "contents"), State('upload-data', 'filename'), State('upload-data', 'last_modified')],
    prevent_initial_call=True
)
def update_hydro(click_data, n_click, start, end, contents, filename, filedate):
    if contents is not None:
        if start > end:
            return {
                'data': [],
                'layout': {}
            }
        if click_data is None:
            location = 1
        else:
            points = click_data['points']
            location = points[0]['location']

        years = xvu.get_target_years(start, end)
        max_basin_row = xvu.hydro_basin_lookup(location, df_ref)
        file_data = xvu.process_file(contents, filename, filedate, years, max_basin_row)[0]
        processed_data = xvu.prepare_data(file_data, df_ref)
        hydro_data = xvu.data_per_year_basin(processed_data, location, years)
        return xvu.plot_hydrograph(hydro_data, location, df_ref)
    else:
        data = []

        layout = {}
        return {
            'data': data,
            'layout': layout
        }


if __name__ == '__main__':
    app.run_server(debug=True)
