# -*- coding: utf-8 -*-
import json
import os
import uuid

import dash
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
import pandas as pd
import seaborn as sns
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from flask_caching import Cache

import xanthosvis.util_functions as xvu

# ----- Define init options and system configuration

# Dash init, define parameters and css information
app = dash.Dash(__name__, external_stylesheets=['assets/base.css', 'assets/custom.css'],
                meta_tags=[{"name": "viewport", "content": "width=device-width"}], suppress_callback_exceptions=True,
                compress=False)

# Set up disk based cache with 100 min timeout
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory',
    "CACHE_DEFAULT_TIMEOUT": 6000
})
server = app.server
root_dir = 'include/'
config = {'displaylogo': False, 'toImageButtonOptions': {
    'format': 'svg',  # one of png, svg, jpeg, webp
    'filename': 'custom_image',
    'height': None,
    'width': None,
    'scale': 1  # Multiply title/legend/axis/canvas sizes by this factor
}}

# Clear cache on load, don't want old files lingering
cache.clear()
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

# reference file to be included in the package data for mapping cells to basins
gridcell_ref_file = os.path.join(root_dir, 'reference', 'xanthos_0p5deg_landcell_reference.csv')

# read in reference file to dataframe
df_ref = pd.read_csv(gridcell_ref_file)

# reference geojson file for basins
basin_json = os.path.join(root_dir, 'reference', 'gcam_basins.geojson')
basin_features = xvu.process_geojson(basin_json)

# World reference file for viewing by country
world_json = os.path.join(root_dir, 'reference', 'world.geojson')
with open(world_json, encoding='utf-8-sig', errors='ignore') as get:
    country_features = json.load(get)

# Available Runoff Statistic for the Choropleth Map
acceptable_statistics = [{'label': 'Mean', 'value': 'mean'}, {'label': 'Median', 'value': 'median'},
                         {'label': 'Min', 'value': 'min'}, {'label': 'Max', 'value': 'max'},
                         {'label': 'Standard Deviation', 'value': 'standard deviation'}]

# ----- End Reference


# ----- HTML Components

app.layout = html.Div(
    children=[
        # Data stores that store a key value for the cache and a select store for remembering selections/persistence
        dcc.Store(id="select_store"),
        dcc.Store(id="data_store", storage_type='memory'),
        dcc.ConfirmDialog(
            id='confirm',
            message='Your data has timed out. Please reload.',
        ),
        html.Div(id="error-message"),

        # Banner/Header Div
        html.Div(
            className="banner row",
            children=[
                html.H2(className="h2-title", children="GCIMS Hydrologic Explorer"),
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
                html.H2(className="h2-title-mobile", children="GCIMS Hydrologic Explorer"),
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
                                                    'height': '35px',
                                                    'lineHeight': '35px',
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
                                    className="form-row",
                                    children=[
                                        html.Div(
                                            style=dict(
                                                width='50%',
                                                verticalAlign="middle"),
                                            children=[
                                                html.H6("Choose Statistic:")
                                            ]
                                        ),

                                        dcc.Dropdown(
                                            id='statistic',
                                            className="loader",
                                            options=[{'label': i['label'], 'value': i['value']} for i in
                                                     acceptable_statistics],
                                            value=acceptable_statistics[0]['value'], clearable=False,
                                            style=dict(
                                                # width='50%',
                                                verticalAlign="middle"
                                            )
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="form-row",
                                    children=[
                                        html.Div(
                                            style=dict(
                                                width='50%',
                                                verticalAlign="middle"),
                                            children=[
                                                html.H6("Choose Units:")
                                            ]
                                        ),

                                        dcc.Dropdown(
                                            id='units',
                                            className="loader",
                                            options=[],
                                            value=None, clearable=False,
                                            style=dict(
                                                # width='50%',
                                                verticalAlign="middle"
                                            )
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="form-row",
                                    children=[
                                        html.Div(
                                            style=dict(
                                                width='50%',
                                                verticalAlign="middle"),
                                            children=[
                                                html.H6("Choose Start Date:"),
                                            ]
                                        ),
                                        dcc.Dropdown(
                                            id='start_year',

                                            className="loader",
                                            options=[],
                                            clearable=False,
                                            style=dict(
                                                # width='50%',
                                                verticalAlign="middle"
                                            )
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="form-row",
                                    children=[
                                        html.Div(
                                            style=dict(
                                                width='50%',
                                                verticalAlign="middle"),
                                            children=[
                                                html.H6("Choose End Date:"),
                                            ]
                                        ),
                                        dcc.Dropdown(
                                            id='through_year',
                                            className="loader",
                                            options=[], clearable=False,
                                            style=dict(
                                                # width='50%',
                                                verticalAlign="middle"
                                            )
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="form-row",
                                    children=[
                                        html.Div(
                                            style=dict(
                                                width='50%',
                                                verticalAlign="middle"),
                                            children=[
                                                html.H6("Choose View By:"),
                                            ]
                                        ),
                                        dcc.RadioItems(
                                            id="area_select",
                                            options=[
                                                {'label': 'GCAM Basin', 'value': 'gcam'},
                                                {'label': 'Country', 'value': 'country'}
                                            ],
                                            value='gcam',
                                            labelStyle={'display': 'inline-block'}
                                        )
                                    ],
                                ),
                                html.Div(
                                    className="padding-top-bot",
                                    children=[
                                        html.H6("Filter by Months:"),
                                        dcc.Dropdown(
                                            id='months_select',
                                            options=[],
                                            multi=True,
                                            style=dict(
                                                height='90px',
                                                width='100%',
                                                verticalAlign="middle"
                                            )
                                        )
                                    ]
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

                # Graphs/Output Div
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
                                                    html.Li("Choose the statistic and associated units you would like "
                                                            "to view"),
                                                    html.Li(
                                                        "Choose the date range from the available start/end dates ("
                                                        "calculated from data upload)"),
                                                    html.Li(
                                                        "Click the 'Load Data' button (also click again after making "
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
                                                        "the 'View as Gridded Data' toggle (note: best used on a subset"
                                                        " of data due to processing time constraints)"),
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
                                        dcc.Loading(id='choro_loader', children=[
                                            dcc.Graph(
                                                id='choro_graph', figure={
                                                    'layout': {
                                                        'title': 'Runoff by Basin (Upload data and click "Load Data")'
                                                    },
                                                    'data': []
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

# @app.callback(Output('choro_graph', 'extendData'),
#               [Input('choro_graph', "relayoutData")],
#               [State("grid_toggle", "on"), State("select_store", 'data'),
#                State("choro_graph", "figure")],
#               )
# def update_markers(relay_data, toggle_value, store_state, fig_info):
#     print("in update markers")
#     click_value = dash.callback_context.triggered[0]['value']
#     click_info = dash.callback_context.triggered[0]['prop_id']
#     if click_info == 'choro_graph.relayoutData':
#         if type(click_value).__name__ == 'dict' and 'mapbox.zoom' in click_value.keys() and toggle_value is True:
#             choro_data = copy.deepcopy(fig_info['data'])
#             choro_data[0]['marker']['size'] = click_value['mapbox.zoom'] * 4
#             # fig_info['data'][0]['radius'] = math.ceil(click_value['mapbox.zoom'] * 3 + 1) mapbox={'zoom': 0.6}
#             return choro_data
#         elif click_value != {'autosize': True}:
#             print("HERE")
#             print(click_value)
#             raise PreventUpdate


# Callback to generate and load the choropleth graph when user clicks load data button, reset button, or selects
# content in the graph for filterinxg

@app.callback([Output("tabs", "value"), Output("grid_toggle", "on"),
               Output("select_store", 'data'), Output('confirm', 'displayed'), Output("choro_graph", "figure")],
              [Input("submit_btn", 'n_clicks'), Input("reset_btn", 'n_clicks'), Input("choro_graph", "selectedData")],
              [State("months_select", "value"), State("grid_toggle", "on"), State("upload-data", "contents"),
               State("upload-data", "filename"), State("upload-data", "last_modified"), State("start_year", "value"),
               State("through_year", "value"), State("statistic", "value"), State("choro_graph", "figure"),
               State("through_year", "options"), State("select_store", 'data'), State("data_store", 'data'),
               State("area_select", "value"), State("units", "value")],
              prevent_initial_call=True)
@cache.memoize(timeout=6000)
def update_choro(load_click, reset_click, selected_data, months, toggle_value, contents, filename,
                 filedate, start, end, statistic, fig_info, through_options, store_state, data_state, area_type, units):
    """Generate choropleth figure based on input values and type of click event

       :param load_click:               Click event data for load button
       :type load_click:                int

       :param reset_click:              Click event data for reset button
       :type reset_click:               int

       :param selected_data             Area select event data for the choropleth graph
       :type selected_data              dict

       :param months                    List of selected months if available
       :type months                     list

       :param toggle_value              Value of grid toggle switch
       :type toggle_value               int

       :param contents:                 Contents of uploaded file
       :type contents:                  str

       :param filename:                 Name of uploaded file
       :type filename:                  list

       :param filedate:                 Date of uploaded file
       :type filedate:                  str

       :param start                     Start year value
       :type start                      str

       :param end                       End year value
       :type end                        str

       :param statistic                 Chosen statistic to run on data
       :type statistic                  str

       :param fig_info                  Current state of figure object
       :type fig_info                   dict

       :param through_options           Current state of figure object
       :type through_options            dict

       :param store_state               Current state of figure object
       :type store_state                dict

       :param data_state                Current state of figure object
       :type data_state                 dict

       :param area_type                 Current state of figure object
       :type area_type                  str

       :param units                     Area select event data for the choropleth graph
       :type units                      str

       :return:                         Active tab, grid toggle value, selection data, warning status, Choropleth figure

       """
    # Don't process anything unless there's contents in the file upload component
    if contents and dash.callback_context.triggered[0]['prop_id'] in ['submit_btn.n_clicks',
                                                                      'choro_graph.selectedData',
                                                                      'choro_graph.relayoutData',
                                                                      'reset_btn.n_clicks']:
        # Check for valid years inputs
        if start > end:
            error_message = html.Div(
                className="alert",
                children=["Invalid Years: Please choose a start year that is less than end year."],
            )
            raise PreventUpdate

        # Get the values of what triggered the callback here
        click_value = dash.callback_context.triggered[0]['value']
        click_info = dash.callback_context.triggered[0]['prop_id']

        # If the user zooms while viewing by grid cell then dynamically adjust marker size for optimal viewing
        # Currently disabled due to performance issues of the relayoutData event triggering too often
        if click_info == 'choro_graph.relayoutData':
            if type(click_value).__name__ == 'dict' and 'mapbox.zoom' in click_value.keys() and toggle_value is True:
                fig_info['data'][0]['marker']['size'] = click_value['mapbox.zoom'] * 4
                # fig_info['data'][0]['radius'] = math.ceil(click_value['mapbox.zoom'] * 3 + 1)
                return 'output_tab', toggle_value, store_state, False, fig_info
            elif click_value != {'autosize': True}:
                print("HERE")
                raise PreventUpdate

        # Get the cached contents of the data  file here instead of rereading every time
        data = cache.get(data_state)
        if data is not None:
            df = data[0]
            file_info = data[1]
        else:
            return 'info_tab', False, store_state, True, fig_info

        # Process inputs (years, data) and set up variables
        year_list = xvu.get_target_years(start, end, through_options)

        # Determine if viewing by country or basin to set up data calls
        df_per_area = None
        if area_type == "gcam":
            if toggle_value is False:
                df_per_area = xvu.data_per_basin(df, statistic, year_list, df_ref, months, filename, units)
                df_per_area['var'] = round(df_per_area['var'], 2)
            features = basin_features
        else:
            if toggle_value is False:
                df_per_area = xvu.data_per_country(df, statistic, year_list, df_ref, months, filename, units)
                df_per_area['var'] = round(df_per_area['var'], 2)
            features = country_features

        # If the user clicked the reset button then reset graph selection store data to empty
        if click_info == 'reset_btn.n_clicks':
            if area_type == "gcam":
                df_per_area = xvu.data_per_basin(df, statistic, year_list, df_ref, months, filename, units)
            else:
                df_per_area = xvu.data_per_country(df, statistic, year_list, df_ref, months, filename, units)
            df_per_area['var'] = round(df_per_area['var'], 2)
            fig = xvu.plot_choropleth(df_per_area, features, mapbox_token, statistic, start, end, file_info, months,
                                      area_type, units)
            store_state = None
            return 'output_tab', False, store_state, False, fig

        # Generate figure based on type of click data (click, area select, or initial load)
        if selected_data is not None and click_info == 'choro_graph.selectedData':
            store_state = selected_data
            if len(selected_data['points']) == 0:
                fig = xvu.plot_choropleth(df_per_area, features, mapbox_token, statistic, start, end, file_info,
                                          months, area_type, units)
            else:
                if toggle_value is True:
                    fig = xvu.update_choro_grid(df_ref, df, features, year_list, mapbox_token, selected_data,
                                                start, end, statistic, file_info, months, area_type, units, filename)
                else:
                    fig = xvu.update_choro_select(df_ref, df_per_area, features, year_list, mapbox_token,
                                                  selected_data, start, end, statistic, file_info, months, area_type,
                                                  units)
        elif click_info == "grid_toggle.on":
            if store_state is None:
                selected_data = None
            if toggle_value is True:
                fig = xvu.update_choro_grid(df_ref, df, features, year_list, mapbox_token, selected_data,
                                            start, end, statistic, file_info, months, area_type, units, filename)
            else:
                fig = xvu.update_choro_select(df_ref, df_per_area, features, year_list, mapbox_token,
                                              selected_data, start, end, statistic, file_info, months, area_type, units)
        else:
            if store_state is None:
                selected_data = None
            if selected_data is not None and len(selected_data['points']) != 0:
                if toggle_value is True:
                    fig = xvu.update_choro_grid(df_ref, df, features, year_list, mapbox_token, selected_data,
                                                start, end, statistic, file_info, months, area_type, units, filename)
                else:
                    fig = xvu.update_choro_select(df_ref, df_per_area, features, year_list, mapbox_token,
                                                  selected_data, start, end, statistic, file_info, months, area_type,
                                                  units)
            else:
                if toggle_value is True:
                    fig = xvu.update_choro_grid(df_ref, df, features, year_list, mapbox_token, selected_data,
                                                start, end, statistic, file_info, months, area_type, units, filename)
                else:
                    fig = xvu.plot_choropleth(df_per_area, features, mapbox_token, statistic, start, end,
                                              file_info, months, area_type, units)

        return 'output_tab', toggle_value, store_state, False, fig

    # If no contents, just return the blank map with instruction
    else:
        raise PreventUpdate


# Callback to set start year options when file is uploaded and store data in disk cache
@app.callback(
    [Output("start_year", "options"), Output("start_year", "value"), Output("upload-data", "children"),
     Output("data_store", 'data'), Output("months_select", "options"), Output("units", "options"),
     Output("units", "value")],
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
        target_years, months_list = xvu.process_input_years(contents, filename, filedate)
        if months_list is None:
            months = []
        else:
            months = xvu.get_available_months(months_list)
        name = filename[0]
        new_text = html.Div(["Using file " + name[:25] + '...' if (len(name) > 25) else "Using file " + name])
        data = xvu.process_file(contents, filename, filedate, years=None)
        xanthos_data = data[0]

        # Create id key for data store and use it as reference
        file_id = str(uuid.uuid4())
        df = xvu.prepare_data(xanthos_data, df_ref)
        data_state = file_id
        cache.set(file_id, [df, data[1]])

        # Evaluate and set unit options
        unit_options = xvu.get_unit_options(data[1])
        if 'km3' in name:
            unit_val = 'km³'
        elif 'mm' in name:
            unit_val = 'mm'
        else:
            unit_val = 'm³/s'
        return target_years, target_years[0]['value'], new_text, data_state, months, unit_options, unit_val


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


# Callback to load the hydro graph when user clicks on choropleth graph
@app.callback(
    Output('hydro_graph', 'figure'),
    [Input('choro_graph', 'clickData'), Input("submit_btn", 'n_clicks')],
    [State('start_year', 'value'), State('through_year', 'value'), State("upload-data", "contents"),
     State('upload-data', 'filename'), State('upload-data', 'last_modified'), State("through_year", "options"),
     State('months_select', 'value'), State('area_select', 'value'), State("hydro_graph", 'figure'),
     State("units", "value"), State("data_store", "data")],
    prevent_initial_call=True
)
def update_hydro(click_data, n_click, start, end, contents, filename, filedate, year_options, months, area_type,
                 hydro_state, units, data_state):
    """Generate choropleth figure based on input values and type of click event

           :param click_data:               Click event data for the choropleth graph
           :type click_data:                dict

           :param n_click                   Submit button click event
           :type n_click                    object

           :param start                     Start year value
           :type start                      str

           :param end                       End year value
           :type end                        str

           :param contents:                 Contents of uploaded file
           :type contents:                  str

           :param filename:                 Name of uploaded file
           :type filename:                  list

           :param filedate:                 Date of uploaded file
           :type filedate:                  str

           :param year_options:             List of year range
           :type year_options:              dict

           :param months:                   List of selected months
           :type months:                    list

           :param area_type:                Indicates if user is viewing by country or basin
           :type area_type:                 str

           :param hydro_state:              Current state of hydro figure
           :type hydro_state:               dict

           :param units:                    Chosen units
           :type units:                     str

           :param data_state:               File cache data
           :type data_state:                dict

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

        # Get data from cache
        data = cache.get(data_state)
        if data is not None:
            df = data[0]
            file_info = data[1]
        else:
            raise PreventUpdate

        # Evaluate chosen area type (basin or country) and set dynamic parameter values
        if area_type == "gcam":
            area_name = "basin_name"
            area_id = "basin_id"
            feature_id = "properties.basin_id"
            area_loc = "basin_id"
            area_title = "Basin"
            area_custom_index = 0
        else:
            area_name = "country_name"
            area_id = "country_id"
            feature_id = "properties.name"
            area_loc = "country_name"
            area_title = "Country"
            area_custom_index = 1

        # Get data from user click
        points = click_data['points']
        context = dash.callback_context.triggered[0]['prop_id']

        # Evaluate current state and only update if user made a different selection
        if context != 'choro_graph.clickData' and 'data' in hydro_state.keys() and len(hydro_state['data']) > 0:
            hydro_type = hydro_state['data'][0]['customdata'][0][0]
            if hydro_type == "basin_id" and area_type == "country":
                raise PreventUpdate
            elif hydro_type == "country_name" and area_type == "gcam":
                raise PreventUpdate

        # Evaluate click event to determine if user clicked on an area or a grid cell
        if 'cell_id' not in points[0]['customdata'].keys():
            location = points[0]['customdata'][area_loc]
            location_type = area_title
        else:
            location = points[0]['customdata']['cell_id']
            location_type = 'cell'

        # Process years, basin/cell information
        years = xvu.get_target_years(start, end, year_options)
        if location_type == 'Basin':
            hydro_data = xvu.data_per_year_area(df, location, years, months, area_loc, filename, units, df_ref)
            return xvu.plot_hydrograph(hydro_data, location, df_ref, 'basin_id', file_info, units)
        elif location_type == 'Country':
            hydro_data = xvu.data_per_year_area(df, location, years, months, area_loc, filename, units, df_ref)
            return xvu.plot_hydrograph(hydro_data, location, df_ref, 'country_name', file_info, units)
        elif location_type == 'cell':
            hydro_data = xvu.data_per_year_cell(df, location, years, months, area_loc, filename, units, df_ref)
            return xvu.plot_hydrograph(hydro_data, location, df_ref, 'grid_id', file_info, units, area_name)

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
    app.run_server(debug=False, threaded=True)
