# -*- coding: utf-8 -*-
import math
import os

import dash
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
import pandas as pd
import seaborn as sns
from dash.dependencies import Input, Output, State
from flask_caching import Cache
from dash.exceptions import PreventUpdate

import xanthosvis.util_functions as xvu

# ----- Define init options and system configuration

# Dash init, define parameters and css information
app = dash.Dash(__name__, external_stylesheets=['assets/base.css', 'assets/custom.css'], show_undo_redo=True,
                meta_tags=[{"name": "viewport", "content": "width=device-width"}], suppress_callback_exceptions=True)
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})
TIMEOUT = 600
server = app.server
root_dir = 'include/'
config = {'displaylogo': False, 'toImageButtonOptions': {
    'format': 'svg',  # one of png, svg, jpeg, webp
    'filename': 'custom_image',
    'height': None,
    'width': None,
    'scale': 1  # Multiply title/legend/axis/canvas sizes by this factor
}}

# Access Token for Mapbox
mapbox_token = open("include/mapbox-token").read()

# Misc Options
sns.set()
group_colors = {"control": "light blue", "reference": "red"}
colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

# ----- End Init


# ----- Reference Files & Global Vars

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

# ----- End Reference


# ----- HTML Components

app.layout = html.Div(
    children=[
        dcc.Store(id="select_store"),
        html.Div(id="error-message"),
        html.Div(
            className="banner row",
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

                                        daq.BooleanSwitch(id="grid_toggle", on=False,
                                                          style={'display': 'inline-block'}),
                                        html.Label(" View as Gridded Data", className="grid-label"),

                                    ],
                                ),
                                html.Div(
                                    className="padding-top-bot",
                                    children=[
                                        html.Button('Load Data', id='submit_btn', n_clicks=0),
                                        html.Button('Reset Graph', id='reset_btn', n_clicks=0),

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
                                                 style={'height': '100%', 'min-height': '490px', 'padding-top':
                                                     '20px', 'padding-left': '15px'}, children=[
                                                html.H6("Loading Data:"),
                                                html.Ol(children=[
                                                    html.Li("Use the 'Data Upload' component to upload Xanthos output "
                                                            "data"),
                                                    html.Li("Choose the statistic you would like to view"),
                                                    html.Li(
                                                        "Choose the year range from the available start/end years ("
                                                        "calculated from data upload)"),
                                                    html.Li(
                                                        "Click the 'Load Data' button (click again after making "
                                                        "any changes to input fields)"),
                                                ]),
                                                html.H6("Filtering Data:"),
                                                html.Ul(children=[
                                                    html.Li(
                                                        "Once data is loaded, to view a subset of basins "
                                                        "use the box select or lasso tool to "
                                                        "select group of basins and rescale the graph"),
                                                    html.Li(
                                                        "To view downscaled 0.5 degree resolution cell data, click "
                                                        "the 'View as Gridded Data' box (note: best used on a subset "
                                                        "of data due to processing time constraints)"),
                                                    html.Li(
                                                        "To reset the graph back to it's initial state, click the "
                                                        "'Reset Graph' button")

                                                ]),
                                            ]),
                                    ]),

                                dcc.Tab(label='Output', value='output_tab', className='custom-tab',
                                        selected_className='custom-tab--selected', children=[
                                        html.Div(
                                            children=[
                                            ]),
                                        dcc.Loading(id='choro_loader',  children=[
                                            dcc.Graph(
                                                id='choro_graph', figure={
                                                    'layout': {
                                                        'title': 'Runoff by Basin (Upload data and click "Load Data")'
                                                    }
                                                }, config=config
                                            )]),
                                        dcc.Loading(id='hydro_loader', children=[
                                            dcc.Graph(
                                                id='hydro_graph', figure={
                                                    'layout': {
                                                        'title': 'Single Basin Runoff per Year (Click on a basin)'
                                                    }
                                                }, config=config
                                            )]
                                                    ),
                                    ]),
                            ]),
                    ],
                ),
            ],
        ),
    ]
)


# ----- End HTML Components

# ----- Dash Callbacks

# Callback to generate and load the choropleth graph when user clicks load data button or toggle grid view
@app.callback([Output("tabs", "value"), Output("grid_toggle", "on"), Output("choro_graph", "figure")],
              [Input("submit_btn", 'n_clicks'), Input("reset_btn", 'n_clicks'),  # Input("choro_graph", 'clickData'),
               Input("choro_graph", "selectedData"), Input("choro_graph", "relayoutData")],
              [State("grid_toggle", "on"), State("upload-data", "contents"), State("upload-data", "filename"),
               State("upload-data", "last_modified"),
               State("start_year", "value"), State("through_year", "value"),
               State("statistic", "value"), State("choro_graph", "figure")],
              prevent_initial_call=True)
def update_choro(load_click, reset_click, selected_data, zoom_data, toggle_value, contents, filename, filedate, start,
                 end,
                 statistic, fig_info):
    """Generate choropleth figure based on input values and type of click event

       :param load_click:               Click event data for load button
       :type load_click:                int

       :param reset_click:             Click event data for reset button
       :type reset_click:              int

       :param selected_data             Area select event data for the choropleth graph
       :type selected_data              dict

       :param toggle_value              Value of grid toggle switch
       :type toggle_value               int

       :param contents:                 Contents of uploaded file
       :type contents:                  str

       :param filename:                 Name of uploaded file
       :type filename:                  str

       :param filedate:                 Date of uploaded file
       :type filedate:                  str

       :param start                     Start year value
       :type start                      int

       :param end                       End year value
       :type end                        int

       :param statistic                 Chosen statistic to run on data
       :type statistic                  str

       :param fig_info                  Current state of figure object
       :type fig_info                   object

       :return:                         Choropleth figure

       """
    # Don't process anything unless there's contents in the file upload component
    if contents:
        # Check for valid inputs
        if start > end:
            error_message = html.Div(
                className="alert",
                children=["Invalid Years: Please choose a start year that is less than end year."],
            )
            return 'info_tab', toggle_value, {
                'data': [],
                'layout': {}
            }

        click_value = dash.callback_context.triggered[0]['value']
        click_info = dash.callback_context. triggered[0]['prop_id']
        if click_info == 'choro_graph.relayoutData':
            if type(click_value).__name__ == 'dict' and 'mapbox.zoom' in click_value.keys() and toggle_value is True:
                fig_info['data'][0]['marker']['size'] = click_value['mapbox.zoom'] * 4.5
                #fig_info['data'][0]['radius'] = math.ceil(click_value['mapbox.zoom'] * 3 + 1)
                return 'output_tab', toggle_value, fig_info
            elif click_value != {'autosize': True}:
                raise PreventUpdate
        # Process inputs (years, data) and set up variables
        year_list = xvu.get_target_years(start, end)
        data = xvu.process_file(contents, filename, filedate, years=year_list)
        xanthos_data = data[0]
        units = data[1]
        df = xvu.prepare_data(xanthos_data, df_ref)
        df_per_basin = xvu.data_per_basin(df, statistic, year_list, df_ref)
        df_per_basin['Runoff (km³)'] = round(df_per_basin['q'], 2)

        if click_info == 'reset_btn.n_clicks':
            fig = xvu.plot_choropleth(df_per_basin, basin_features, mapbox_token, statistic, start, end, units)
            return 'output_tab', False, fig

        # Generate figure based on type of click data (click, area select, or initial load)
        # if graph_click is not None and click_info == 'choro_graph.clickData':
        #     fig = xvu.update_choro_click(df_ref, df_per_basin, basin_features, mapbox_token, graph_click, start, end,
        #                                  statistic, units)

        if selected_data is not None and click_info == 'choro_graph.selectedData':
            if len(selected_data['points']) == 0:
                fig = xvu.plot_choropleth(df_per_basin, basin_features, mapbox_token, statistic, start, end, units)
            else:
                if toggle_value is True:
                    fig = xvu.update_choro_grid(df_ref, df, basin_features, year_list, mapbox_token, selected_data,
                                                start, end, statistic, units)
                else:
                    fig = xvu.update_choro_select(df_ref, df_per_basin, basin_features, year_list, mapbox_token,
                                                  selected_data, start, end, statistic, units)

        elif click_info == "grid_toggle.on":
            if toggle_value is True:
                fig = xvu.update_choro_grid(df_ref, df, basin_features, year_list, mapbox_token, selected_data,
                                            start, end, statistic, units)
            else:
                fig = xvu.update_choro_select(df_ref, df_per_basin, basin_features, year_list, mapbox_token,
                                              selected_data, start, end, statistic, units)
        else:
            if selected_data is not None and len(selected_data['points']) != 0:
                if toggle_value is True:
                    fig = xvu.update_choro_grid(df_ref, df, basin_features, year_list, mapbox_token, selected_data,
                                                start, end, statistic, units)
                else:
                    fig = xvu.update_choro_select(df_ref, df_per_basin, basin_features, year_list, mapbox_token,
                                                  selected_data, start, end, statistic, units)
            else:
                if toggle_value is True:
                    fig = xvu.update_choro_grid(df_ref, df, basin_features, year_list, mapbox_token, selected_data,
                                                start, end, statistic, units)
                else:
                    fig = xvu.plot_choropleth(df_per_basin, basin_features, mapbox_token, statistic, start, end, units)

        return 'output_tab', toggle_value, fig

    # If no contents, just return the blank map with instruction
    else:
        data = []

        layout = {'title': 'Runoff by Basin (Upload data and click "View Data'}
        return 'info_tab', toggle_value, {
                   'data': data,
                   'layout': layout
               }

    # Callback to set start year options when file is uploaded and store data in upload component contents


@app.callback(
    [Output("start_year", "options"), Output("start_year", "value"), Output("upload-data", "children")],
    [Input("upload-data", "contents")], [State('upload-data', 'filename'), State('upload-data', 'last_modified')],
    prevent_initial_call=True
)
def update_options(contents, filename, filedate):
    """Set start year options based on uploaded file's data

           :param contents:                 Contents of uploaded file
           :type contents:                  str

           :param filename:                 Name of uploaded file
           :type filename:                  str

           :param filedate:                 Date of uploaded file
           :type filedate:                  str

           :return:                         Options list, initial value, new upload component text

    """
    # Check if there is uploaded content
    if contents:
        # Process contents for available years
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
    """Assign through/end year options based on the start year options and value

           :param value:                    Start year's selected value
           :type value:                     int

           :param options:                  Start year's option list
           :type options:                   dataframe

           :param current_value:            Current value of through_year, if any
           :type current_value:             int

           :return:                         Through/end year options and initial value

    """
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
    """Generate choropleth figure based on input values and type of click event

           :param click_data:               Click event data for the choropleth graph
           :type click_data:                dict

           :param n_click                   Submit button click event
           :type n_click                    object

           :param start                     Start year value
           :type start                      int

           :param end                       End year value
           :type end                        int

           :param contents:                 Contents of uploaded file
           :type contents:                  str

           :param filename:                 Name of uploaded file
           :type filename:                  str

           :param filedate:                 Date of uploaded file
           :type filedate:                  str

           :return:                         Choropleth figure

    """
    if contents is not None:
        # If invalid end date then don't do anything and output message
        if start >= end:
            return {
                'data': [],
                'layout': {
                    'title': 'Please choose an end year that is greater than the start year'
                }
            }
        # If there wasn't a click event on choro graph then do not load new hydro graph
        if click_data is None:
            return {
                'data': [],
                'layout': {
                    'title': 'Single Basin Data per Year (Click on a basin to load)'
                }
            }
        # Get data from user click
        else:
            points = click_data['points']
            if points[0]['customdata'].__class__ == int:
                location = points[0]['customdata']
                location_type = 'basin'
            else:
                location = points[0]['customdata'][1]
                location_type = 'cell'

        # Process years, basin/cell information
        years = xvu.get_target_years(start, end)
        if location_type == 'basin':
            max_basin_row = xvu.hydro_basin_lookup(location, df_ref)
            file_data = xvu.process_file(contents, filename, filedate, years, max_basin_row)[0]
            processed_data = xvu.prepare_data(file_data, df_ref)
            hydro_data = xvu.data_per_year_basin(processed_data, location, years)
            return xvu.plot_hydrograph(hydro_data, location, df_ref, 'basin')
        elif location_type == 'cell':
            max_cell_row = xvu.hydro_cell_lookup(location, df_ref)
            file_data = xvu.process_file(contents, filename, filedate, years, max_cell_row)[0]
            processed_data = xvu.prepare_data(file_data, df_ref)
            hydro_data = xvu.data_per_year_cell(processed_data, location, years)
            return xvu.plot_hydrograph(hydro_data, location, df_ref, 'cell')
    # Return nothing if there's no uploaded contents
    else:
        data = []

        layout = {}
        return {
            'data': data,
            'layout': layout
        }


# ----- End Dash Callbacks

# Start Dash Server
if __name__ == '__main__':
    app.run_server(debug=True, threaded=True)
