# -*- coding: utf-8 -*-
import os

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import seaborn as sns
from dash.dependencies import Input, Output, State

import xanthosvis.util_functions as xvu

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
                                        dcc.Loading(id='file_loader', children=[
                                            dcc.Upload(
                                                id='upload-data',
                                                className="loader",
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
                                            )]),
                                    ],
                                ),
                                html.Div(
                                    className="padding-top-bot",
                                    children=[
                                        html.H6("Choose Statistic:"),
                                        dcc.Dropdown(
                                            id='statistic',
                                            className="loader",
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
                                            className="loader",
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
                                            className="loader",
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
                                    className="xanthos-div",
                                    children=[
                                        html.A(
                                            [html.Img(src="assets/GitHub-Mark-Light-32px.png", className="xanthos-img"),
                                             "Find Xanthos on GitHub"],
                                            href="https://github.com/JGCRI/xanthos",
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
                        dcc.Tabs(id='tabs', value="info_tab", parent_className='custom-tabs',
                                 className='custom-tabs-container loader', children=[
                                dcc.Tab(label='Instructions', value='info_tab', className='custom-tab',
                                        selected_className='custom-tab--selected', children=[
                                        html.Div(id='tab1_content', className="bg-white",
                                                 style={'height': '100%', 'min-height': '490px', 'padding-top': '20px',
                                                        'padding-left': '15px'}, children=[
                                                html.H6("How to Use the System:"),
                                                html.Ol(children=[
                                                    html.Li(
                                                        "Use the 'Data Upload' component to upload Xanthos output data"),
                                                    html.Li("Choose the statistic you would like to view"),
                                                    html.Li(
                                                        "Choose the year range from the available start/end years (calculated "
                                                        "from data upload)"),
                                                    html.Li(
                                                        "Click the 'View Data' button (also click again if there are changes "
                                                        "to any of the fields)"),
                                                    html.Li(
                                                        "To view an individual basin's data, click the basin on the map")
                                                ]),
                                            ]),
                                    ]),

                                dcc.Tab(label='Output', value='output_tab', className='custom-tab',
                                        selected_className='custom-tab--selected', children=[
                                        dcc.Loading(id='choro_loader', children=[
                                            dcc.Graph(
                                                id='choro_graph', figure={
                                                    'layout': {
                                                        'title': 'Runoff by Basin (Upload data and click "View Data")'
                                                    }
                                                }  # , config={'modeBarButtonsToRemove': ['select2d', 'lasso2d']}
                                            )]),
                                        dcc.Loading(id='hydro_loader', children=[
                                            dcc.Graph(
                                                id='hydro_graph', figure={
                                                    'layout': {
                                                        'title': 'Single Basin Runoff per Year (Click on a basin)'
                                                    }
                                                }
                                            )]),
                                    ]),
                            ]),
                    ],
                ),
            ],
        ),
    ]
)


# Callback to generate and load the choropleth graph when user clicks load data button
@app.callback([Output("tabs", "value"), Output("choro_graph", "figure")],
              [Input("submit_btn", 'n_clicks'), Input("choro_graph", 'clickData'),
               Input("choro_graph", "selectedData")],
              [State("upload-data", "contents"), State("upload-data", "filename"),
               State("upload-data", "last_modified"),
               State("start_year", "value"), State("through_year", "value"),
               State("statistic", "value")],
              prevent_initial_call=True)
def update_choro(click, graph_click, selected_data, contents, filename, filedate, start, end, statistic):
    if contents:
        if start > end:
            error_message = html.Div(
                className="alert",
                children=["Invalid Years: Please choose a start year that is less than end year."],
            )
            return 'info_tab', {
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

        click_info = dash.callback_context.triggered[0]['prop_id']

        if graph_click is not None and click_info == 'choro_graph.clickData':
            basin_id = graph_click['points'][0]['customdata']
            subset = df_ref[df_ref['basin_id'] == basin_id]
            lon_min = subset['longitude'].min()
            lon_max = subset['longitude'].max()
            lat_min = subset['latitude'].min()
            lat_max = subset['latitude'].max()
            lon = (lon_min + lon_max) / 2
            lat = (lat_min + lat_max) / 2
            basin_subset = list(set(df_ref[((df_ref['longitude'] >= lon_min) &
                                            (df_ref['longitude'] <= lon_max) &
                                            (df_ref['latitude'] >= lat_min) &
                                            (df_ref['latitude'] <= lat_max))][
                                        'basin_id']))
            df_per_basin = df_per_basin[df_per_basin['basin_id'].isin(basin_subset)]
            # df_per_basin = df_per_basin[df_per_basin['basin_id'] == basin_id]

        elif selected_data is not None and click_info == 'choro_graph.selectedData':
            # basin_id = selected_data['points'][0]['location']
            basin_id = [i['location'] for i in selected_data['points']]
            df = df[df['basin_id'].isin(basin_id)]
            df_selected = xvu.data_per_cell(df, statistic, year_list, df_ref)
            df_selected['Runoff (km³)'] = round(df_selected['q'], 2)
            lon_min = df_selected['longitude'].min()
            lon_max = df_selected['longitude'].max()
            lat_min = df_selected['latitude'].min()
            lat_max = df_selected['latitude'].max()
            lon = (lon_min + lon_max) / 2
            lat = (lat_min + lat_max) / 2
            # df_per_basin = xvu.data_per_cell(df, statistic, year_list, df_ref_sub)
            fig = go.Figure(go.Scattermapbox(lat=df_selected['latitude'], lon=df_selected['longitude'],
                                             mode='markers', customdata=df['basin_id'],
                                             text=df_selected.apply(lambda row: f"<b>{row['basin_name']}</b><br>"
                                                                                f"ID: {row['basin_id']}<br>"
                                                                                f"Grid Cell: {row['id']}<br><br>"
                                                                                f"Runoff (km³): {row['Runoff (km³)']} "
                                                                                f"({statistic})",
                                                                    axis=1), hoverinfo="text",
                                             marker=go.scattermapbox.Marker(
                                                 size=8,
                                                 color=df_selected['Runoff (km³)'],
                                                 opacity=0.4,
                                                 showscale=True
                                             )
                                             ))
            fig.update_layout(
                title={
                    'text': f"<b>Runoff ({statistic}) by Basin {start} - {end}</b>",
                    'y': 0.94,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': dict(
                        family='Roboto',
                        size=20
                    ),
                },
                margin=go.layout.Margin(
                    l=30,  # left margin
                    r=10,  # right margin
                    b=10,  # bottom margin
                    t=60  # top margin
                ),
                mapbox_style="mapbox://styles/jevanoff/ckckto2j900k01iomsh1f8i20",
                mapbox_accesstoken=mapbox_token, mapbox={'center': {'lat': lat, 'lon': lon}, 'zoom': 2}
            )

            return 'output_tab', fig

        fig = go.Figure(go.Choroplethmapbox(geojson=basin_features, locations=df_per_basin.basin_id,
                                            z=df_per_basin['Runoff (km³)'].astype(str), marker_opacity=0.7,
                                            text=df_per_basin.apply(lambda row: f"<b>{row['basin_name']}</b><br>"
                                                                                f"ID: {row['basin_id']}<br><br>"
                                                                                f"Runoff (km³): {row['Runoff (km³)']} "
                                                                                f"({statistic})",
                                                                    axis=1), colorscale="Plasma",
                                            featureidkey="properties.basin_id", legendgroup="Runoff",
                                            hoverinfo="text", colorbar={'separatethousands': True, 'tickformat': ","},
                                            customdata=df_per_basin['basin_id']))

        fig.update_layout(
            title={
                'text': f"<b>Runoff ({statistic}) by Basin {start} - {end}</b>",
                'y': 0.94,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(
                    family='Roboto',
                    size=20
                ),
            },
            margin=go.layout.Margin(
                l=30,  # left margin
                r=10,  # right margin
                b=10,  # bottom margin
                t=60  # top margin
            ),
            mapbox_style="mapbox://styles/jevanoff/ckckto2j900k01iomsh1f8i20",
            mapbox_accesstoken=mapbox_token, mapbox={'zoom': 0}
        )

        if graph_click is not None and click_info == 'choro_graph.clickData':
            fig.update_layout(mapbox={'center': {'lat': lat, 'lon': lon}, 'zoom': 2})

        return 'output_tab', fig

    else:
        data = []

        layout = {}
        return 'info_tab', {
            'data': data,
            'layout': layout
        }


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
        if len([i for i in options if i['value'] == current_value]) >= 1:
            new_value = current_value
        else:
            new_value = options[len(options) - 1]['value']

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
        if start >= end:
            return {
                'data': [],
                'layout': {
                    'title': 'Please choose an end year that is greater than the start year'
                }
            }
        if click_data is None:
            return {
                'data': [],
                'layout': {
                    'title': 'Single Basin Data per Year (Click on a basin to load)'
                }
            }
        else:
            points = click_data['points']
            location = points[0]['customdata']

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
