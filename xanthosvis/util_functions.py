import base64
import collections
import datetime
import io
import json
from zipfile import ZipFile

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go


def get_available_years(in_file, non_year_fields=None):
    """Get available years from file.  Reads only the header from the file and returns years and months from file.

    :params in_file:               Processed file as a dataframe
    :type in_file:                 dataframe

    :param non_year_fields:        list of non-year fields to drop from the file
    :type non_year_fields:         list

    :return:                       list of years and list of months

    """

    # drop non-year fields
    if non_year_fields is None:
        non_year_fields = ['id']
    in_file.drop(columns=non_year_fields, inplace=True)

    # Build years and months list
    year_list = list()
    year_list = [{'label': i if len(i) == 4 else i[0:4] + '-' + i[4:6], 'value': i} for i in in_file.columns]
    month_list = list()

    if len(in_file.columns[0]) == 6:
        month_list = np.unique([i[4:6] for i in in_file.columns])
    else:
        month_list = None
    return year_list, month_list


def get_available_months(months_list):
    """Parse out months from xanthos output format of '198001' which is year 1980 month 1

        :params months_list:           list of dates parsed from file
        :type months_list:             list

        :return:                       list of months available for months form control

    """

    # Parse list to determine which months it contains
    months = list()
    if "01" in months_list:
        months.append({'label': "January", 'value': "01"})
    if "02" in months_list:
        months.append({'label': "February", 'value': "02"})
    if "03" in months_list:
        months.append({'label': "March", 'value': "03"})
    if "04" in months_list:
        months.append({'label': "April", 'value': "04"})
    if "05" in months_list:
        months.append({'label': "May", 'value': "05"})
    if "06" in months_list:
        months.append({'label': "June", 'value': "06"})
    if "07" in months_list:
        months.append({'label': "July", 'value': "07"})
    if "08" in months_list:
        months.append({'label': "August", 'value': "08"})
    if "09" in months_list:
        months.append({'label': "September", 'value': "09"})
    if "10" in months_list:
        months.append({'label': "October", 'value': "10"})
    if "11" in months_list:
        months.append({'label': "November", 'value': "11"})
    if "12" in months_list:
        months.append({'label': "December", 'value': "12"})

    return months


def available_through_years(available_year_list, start_year):
    """Return a list of available through/ending years that are >= the start year.

    :param available_year_list:            List of available years from the input file
    :type available_year_list:             list

    :param start_year:                     The start year chosen
    :type start_year:                      int

    :return:                               list of available through/ending years

    """

    # Construct options for drop down based on input parameters
    options = []
    for i in available_year_list:
        if int(i['value']) >= int(start_year):
            options.append(i)
    return options


def basin_to_gridcell_dict(df_reference):
    """Generate a dictionary of gridcell id to basin id {grid_id: basin_id}

    :param df_reference:            Input data reference dataframe containing grid to basin info
    :type df_reference:             dataframe

    :return:                        dict. {grid_id: basin_id}

    """

    # select target fields
    df_reference = df_reference[['grid_id', 'basin_id']]

    # set index that will become dictionary key
    df_reference.set_index('grid_id', inplace=True)

    return df_reference.to_dict()['basin_id']


def country_to_gridcell_dict(df_reference):
    """Generate a dictionary of gridcell id to basin id {grid_id: basin_id}

    :param df_reference:            Input data reference dataframe containing grid to country info
    :type df_reference:             dataframe

    :return:                        dict. {grid_id: basin_id}

    """

    # select target fields
    df_reference = df_reference[['grid_id', 'country_id', 'country_name', 'area_hectares']]

    # set index that will become dictionary key
    df_reference.set_index('grid_id', inplace=True)

    return df_reference.to_dict()


def prepare_data(df, df_ref):
    """Process dataframe to add the basin id from reference file.

    :param df:                      Processed dataframe
    :type df:                       dataframe

    :param df_ref:                  Reference data frame from package
    :type df_ref:                   dataframe

    :return:                        dataframe; data with basin id

    """

    # get dictionary of grid id to basin id
    grid_basin_dict = basin_to_gridcell_dict(df_ref)

    # get country mapping
    grid_country_dict = country_to_gridcell_dict(df_ref)

    # add basin id, country_name, country_id, and area via mappings
    df['basin_id'] = df['id'].map(grid_basin_dict)
    df['country_name'] = df['id'].map(grid_country_dict['country_name'])
    df['country_id'] = df['id'].map(grid_country_dict['country_id'])
    df['area'] = df['id'].map(grid_country_dict['area_hectares'])

    return df


def data_per_basin(df, statistic, yr_list, df_ref, months, filename, units):
    """Generate a data frame representing data per basin for all years
    represented by an input statistic.

    :param df:                      Data with basin id
    :type df:                       dataframe

    :param statistic:               statistic name from user input
    :type statistic:                str

    :param yr_list:                 List of years to process
    :type yr_list:                  list

    :param df_ref                   Reference dataframe
    :type df_ref                    dataframe

    :param months                   parameter for filtering by months
    :type months                    list

    :param filename                 Name of input file for parsing
    :type filename                  list

    :param units                    Chosen units for output
    :type units                     str

    :return:                        dataframe; grouped by basin for statistic

    """

    if months is not None and len(months) > 0:
        yr_list = [c for c in yr_list if c[4:6] in months]

    # sum data by basin by year
    grp = df.groupby('basin_id').sum()

    grp.drop(columns=['id'], inplace=True)

    # calculate chosen statistic
    if statistic == 'mean':
        grp['var'] = grp[yr_list].mean(axis=1)

    elif statistic == 'median':
        grp['var'] = grp[yr_list].median(axis=1)

    elif statistic == 'min':
        grp['var'] = grp[yr_list].min(axis=1)

    elif statistic == 'max':
        grp['var'] = grp[yr_list].max(axis=1)

    elif statistic == 'standard deviation':
        grp['var'] = grp[yr_list].std(axis=1)

    else:
        msg = f"The statistic requested '{statistic}' is not a valid option."
        raise ValueError(msg)

    # Parse out and convert units if necessary
    unit_type = get_units_from_name(filename)
    if unit_type != units:
        if unit_type == 'km³':
            grp['var'] = (grp['var'] * 1000000) / (grp['area'] / 100)
    if unit_type == 'mm':
        grp['var'] = (grp['var'] / 1000000) * (grp['area'] / 100)

    #  Drop unneeded columns
    grp.drop(columns=yr_list, inplace=True)

    # Map basin and country fields using df_ref
    grp.reset_index(inplace=True)
    mapping = dict(df_ref[['basin_id', 'basin_name']].values)
    mapping2 = df_ref.groupby('basin_id')[['country_id']].apply(lambda g: g.country_id.unique().tolist()).to_dict()
    mapping3 = df_ref.groupby('basin_id')[['country_name']].apply(lambda g: g.country_name.unique().tolist()).to_dict()
    grp['basin_name'] = grp.basin_id.map(mapping)
    grp['country_id'] = grp.basin_id.map(mapping2)
    grp['country_name'] = grp.basin_id.map(mapping3)

    return grp


def data_per_cell(df, statistic, yr_list, df_ref, months, area_type, unit_type, units):
    """Generate a data frame representing data per grid cell for years/months chosen

    :param df:                      Data with basin id
    :type df:                       dataframe

    :param statistic:               statistic name from user input
    :type statistic:                str

    :param yr_list:                 List of years to process
    :type yr_list:                  list

    :param df_ref                   Reference dataframe
    :type df_ref                    dataframe

    :param months                   months from dropdown
    :type months                    list

    :param area_type                Type of area (country or basin)
    :type area_type                 str

    :param unit_type                Units chosen by user
    :type unit_type                 str

    :param units                    Base unit parsed from file
    :type units                     str

    :return:                        dataframe; grouped by area for statistic

    """
    if months is not None and len(months) > 0:
        yr_list = [c for c in yr_list if c[4:6] in months]

    # Set up column list for joins
    column_list = list(df)
    column_list.remove('id')
    column_list.remove('basin_id')

    # Sum data by basin by year
    df_ref = df_ref.set_index('grid_id')
    df = df.join(df_ref, 'id', 'left', 'a1')

    # Calculate stat
    if statistic == 'mean':
        df['var'] = df[yr_list].mean(axis=1)

    elif statistic == 'median':
        df['var'] = df[yr_list].median(axis=1)

    elif statistic == 'min':
        df['var'] = df[yr_list].min(axis=1)

    elif statistic == 'max':
        df['var'] = df[yr_list].max(axis=1)

    elif statistic == 'standard deviation':
        df['var'] = df[yr_list].std(axis=1)

    else:
        msg = f"The statistic requested '{statistic}' is not a valid option."
        raise ValueError(msg)

    # Convert units if user has chosen different from file default
    if unit_type != units:
        if unit_type == 'km³':
            df['var'] = (df['var'] * 1000000) / (df['area'] / 100)
    if unit_type == 'mm':
        df['var'] = (df['var'] / 1000000) * (df['area'] / 100)

    return df


def data_per_country(df, statistic, yr_list, df_ref, months, filename, units):
    """Generate a data frame representing data per country for all years/months
    represented by an input statistic.

    :param df:                      Data with basin id
    :type df:                       dataframe

    :param statistic:               statistic name from user input
    :type statistic:                str

    :param yr_list:                 List of years to process
    :type yr_list:                  list

    :param df_ref                   Reference dataframe
    :type df_ref                    dataframe

    :param months                   months from dropdown
    :type months                    list

    :param filename                 Name of uploaded file
    :type filename                  list

    :param units                    Chosen unit type
    :type units                     str

    :return:                        dataframe; grouped by country for statistic

    """

    if months is not None and len(months) > 0:
        yr_list = [c for c in yr_list if c[4:6] in months]

    # sum data by basin by year
    grp = df.groupby('country_name').sum()

    grp.drop(columns=['id'], inplace=True)

    # calculate statistic
    if statistic == 'mean':
        grp['var'] = grp[yr_list].mean(axis=1)

    elif statistic == 'median':
        grp['var'] = grp[yr_list].median(axis=1)

    elif statistic == 'min':
        grp['var'] = grp[yr_list].min(axis=1)

    elif statistic == 'max':
        grp['var'] = grp[yr_list].max(axis=1)

    elif statistic == 'standard deviation':
        grp['var'] = grp[yr_list].std(axis=1)

    else:
        msg = f"The statistic requested '{statistic}' is not a valid option."
        raise ValueError(msg)

    #  Drop unneeded columns
    grp.drop(columns=yr_list, inplace=True)

    # Convert units if necessary
    unit_type = get_units_from_name(filename)
    if unit_type != units:
        if unit_type == 'km³':
            grp['var'] = (grp['var'] * 1000000) / (grp['area'] / 100)
    if unit_type == 'mm':
        grp['var'] = (grp['var'] / 1000000) * (grp['area'] / 100)

    # Map country values using df_ref
    grp.reset_index(inplace=True)
    mapping = dict(df_ref[['country_name', 'country_id']].values)
    grp['country_id'] = grp.country_name.map(mapping)
    mapping2 = df_ref.groupby('country_name')[['basin_id']].apply(lambda g: g.basin_id.unique().tolist()).to_dict()
    grp['basin_id'] = grp.country_name.map(mapping2)
    return grp


def data_per_year_area(df, area_id, yr_list, months, area_type, filename, units, df_ref):
    """Generate a data frame representing the sum of the data per year for an area

    :param df:                     input data having data per year
    :type df:                      dataframe

    :param area_id:                id of area to filter and aggregate data for
    :type area_id:                 int

    :param yr_list                 list of years to consider
    :type yr_list                  list

    :param months                  months from dropdown
    :type months                   list

    :param area_type               Type of area (country or basin)
    :type area_type                str

    :param filename                Name of uploaded file
    :type filename                 list

    :param units                   Chosen unit type
    :type units                    str

    :param df_ref                  Reference file dataframe
    :type df_ref                   dataframe

    :return:                       dataframe; sum values per year for a target basin

    """

    if months is not None and len(months) > 0:
        yr_list = [c for c in yr_list if c[4:6] in months]

    # Sum data by basin by year
    grp = df.groupby(area_type).sum()

    # Adjust columns and reset index
    grp.drop(columns=['id'], inplace=True)
    grp = grp[yr_list]
    grp.reset_index(inplace=True)

    # Get only target basin_id
    dfx = grp.loc[grp[area_type] == area_id].copy()

    # Adjust return DF columns and reset index
    dfx.drop(columns=[area_type], inplace=True)
    df = dfx.T.copy()
    df.reset_index(inplace=True)
    df.columns = ['Year', 'var']

    unit_type = get_units_from_name(filename)
    area = 0

    # Convert units if necessary
    if unit_type != units:
        area = df_ref[df_ref[area_type] == area_id]['area_hectares'].sum()
        if unit_type == 'km³':
            df['var'] = (df['var'] * 1000000) / (area / 100)
    if unit_type == 'mm':
        df['var'] = (df['var'] / 1000000) * (area / 100)

    return df


def data_per_year_cell(df, cell_id, yr_list, months, area_type, filename, units, df_ref):
    """Generate a data frame representing the sum of the data per year for a target grid cell.

    :param df:                      input data having data per year
    :type df:                       dataframe

    :param cell_id:                 id of grid cell to filter and aggregate data for
    :type cell_id:                  int

    :param yr_list                  list of years to consider
    :type yr_list                   list

    :param months                   months from dropdown
    :type months                    list

    :param area_type                Type of area (country or basin)
    :type area_type                 str

    :param filename                 Name of input file
    :type filename                  list

    :param units                    Units chosen by user
    :type units                     str

    :param df_ref                   Reference dataframe
    :type df_ref                    dataframe

    :return:                        dataframe; sum values per year for a target basin

    """

    if months is not None and len(months) > 0:
        yr_list = [c for c in yr_list if c[4:6] in months]

    keep_cols = yr_list

    # Get only target grid cell
    df = df[df['id'] == cell_id].copy()

    # Adjust columns and reset index
    df.drop(columns=['basin_id', 'id'], inplace=True)
    df = df[keep_cols]
    df = df.T.copy()

    # Adjust return DF columns and reset index
    df.reset_index(inplace=True)
    df.columns = ['Year', 'var']

    unit_type = get_units_from_name(filename)
    area = 0

    # Convert units if necessary
    if unit_type != units:
        area = df_ref[df_ref['grid_id'] == cell_id]['area_hectares'].values[0]
        if unit_type == 'km³':
            df['var'] = (df['var'] * 1000000) / (area / 100)
    if unit_type == 'mm':
        df['var'] = (df['var'] / 1000000) * (area / 100)

    return df


def process_geojson(in_file):
    """Read in geojson spatial data and add in a feature level id.

    :param in_file:                 Full path with file name and extension to the input geojson file
    :type in_file:                  str

    :return:                        geojson array

    """

    # Open file and load data
    with open(in_file) as get:
        basin_features = json.load(get)

    # Add in basin_id
    for fx in basin_features['features']:
        fx['id'] = fx['properties']['basin_id']

    return basin_features


def get_unit_info(units):
    """Read in split file name and return data variable type (runoff, AET, etc)

        :param units:                Name of file
        :type units:                 list

        :return:                     str; Name of variable

        """

    if units[0] == "q":
        data_type = "Runoff"
    elif units[0] == "avgchflow":
        data_type = "Streamflow"
    elif units[0] == "aet":
        data_type = "Actual ET"
    elif units[0] == "pet":
        data_type = "Potential ET"
    else:
        data_type = "unknown"

    return data_type


def get_unit_options(file_info):
    """Get options for units based on data variable (runoff, PET, etc)

        :param file_info:               Name of file
        :type file_info:                list

        :return:                        dict; list of unit options for dropdown

        """

    options = list()
    if file_info[0] == "avgchflow":
        options.append({'label': "m³/s", 'value': "m³/s"})
    else:
        options.append({'label': "km³", 'value': "km³"})
        options.append({'label': "mm", 'value': "mm"})

    return options


def get_units_from_name(filename):
    """Get base unit type from file to compare to chosen unit type

        :param filename:                Name of file
        :type filename:                 list

        :return:                        str; unit type parsed from file

        """

    if 'km3' in filename[0]:
        unit_val = 'km³'
    elif 'mm' in filename[0]:
        unit_val = 'mm'
    else:
        unit_val = 'm3'
    return unit_val


def plot_choropleth(df_per_area, features, mapbox_token, statistic, start, end, file_info, months, area_type, units):
    """Plot interactive choropleth map grouped by country or basin

    :param df_per_area:             dataframe with area level stats
    :type df_per_area:              dataframe

    :param features:                geojson spatial data and area id field
    :type features:                 dataframe

    :param mapbox_token             Access token for mapbox
    :type mapbox_token              str

    :param statistic                Chosen statistic to run on data
    :type statistic                 str

    :param start                    beginning year
    :type start                     number

    :param end                      ending year
    :type end                       number

    :param file_info                Name of uploaded file
    :type file_info                 list

    :param months                   Selected months
    :type months                    list

    :param area_type                Country or basin
    :type area_type                 str

    :param units:                   Unit of measurement
    :type units:                    str

    """

    # Get base units from filename
    unit_type = get_unit_info(file_info)

    # Set local variables based on area type (country or basin)
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

    # Set up list to hold per item custom data for easy access
    custom_data = [{'basin_id': x, 'country_id': y, 'country_name': z} for x, y, z in
                   zip(df_per_area['basin_id'], df_per_area['country_id'], df_per_area['country_name'])]
    custom_data[1] = area_type

    # Main output figure - generates a choroplethmapbox figure
    fig = go.Figure(go.Choroplethmapbox(geojson=features, locations=df_per_area[area_loc],
                                        z=df_per_area['var'].astype(str), marker=dict(opacity=0.7),
                                        text=df_per_area.apply(lambda row: f"<b>{row[area_name]}</b><br>"
                                                                           f"ID: {row[area_id]}<br><br>"
                                                                           f"{unit_type} ({units}): {row['var']} "
                                                                           f"({statistic})",
                                                               axis=1), colorscale="Plasma",
                                        featureidkey=feature_id, legendgroup="Runoff",
                                        hoverinfo="text",
                                        colorbar={'separatethousands': True, 'tickformat': ",",
                                                  'title': unit_type + ' ' + '(' + units + ')'},
                                        customdata=custom_data))

    # Add in additional layout options to figure
    fig.update_layout(
        title={
            'text': f"<b>{unit_type} ({statistic}) by {area_title} {start if len(start) <= 4 else start[0:4] + '-' + start[4:6]} - "
                    f"{end if len(end) <= 4 else end[0:4] + '-' + end[4:6]}</b>",
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
        mapbox_accesstoken=mapbox_token, mapbox={'zoom': 0.6}
    )

    return fig


def plot_hydrograph(df, selection_id, df_ref, id_type, file_info, units, area_label=""):
    """Plot a hydrograph of a specific basin, country or grid cell.

    :param df:                      Input dataframe with data and area id for a target area
    :type df:                       dataframe

    :param selection_id:            ID of selected area
    :type selection_id:             int

    :param df_ref:                  Reference dataframe with gis data
    :type df_ref                    dataframe

    :param id_type:                 Type of ID passed, area or cell
    :type id_type                   str

    :param file_info                Name of uploaded file
    :type file_info                 str

    :param units                    Chosen unit type
    :type units                     str

    :param area_label               Area label
    :type area_label                str

    """

    # Process dataframe and set up variables
    df['var'] = round(df['var'], 2)
    title_text = ""
    tick_format = ""
    if len(df['Year'][0]) > 4:
        df['Year'] = [datetime.datetime.strptime(i, "%Y%m") for i in df['Year']]
        time_type = 'Month'
    else:
        time_type = 'Year'

    # Check for how many items in data, if over 40 then only display up to 40 X-axis points
    nticks = len(df)
    if nticks > 40:
        nticks = 40

    # Process data and set up graphing fields based on type of id (cell, basin, country)
    if id_type == 'basin_id':
        df_area = df_ref[df_ref['basin_id'] == selection_id][0:1]
        df_area = df_area['basin_name']
        area_label = df_area.iat[0]
        title_text = {
            'text': f"<b>Basin {selection_id}: {area_label} - {units} per {time_type}</b>",
            'y': 0.92,
            'x': 0.48,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(
                family='Roboto',
                size=20
            ),
        }
        tick_format = ','
    elif id_type == 'country_name':
        df_area = df_ref[df_ref['country_name'] == selection_id][0:1]
        df_area = df_area['country_name']
        area_label = df_area.iat[0]
        title_text = {
            'text': f"<b>Country: {selection_id} - {units} per {time_type}</b>",
            'y': 0.92,
            'x': 0.48,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(
                family='Roboto',
                size=20
            ),
        }
        tick_format = ','
    elif id_type == 'grid_id':
        area_label = df_ref[df_ref['grid_id'] == selection_id][area_label].iat[0]
        title_text = {
            'text': f"<b>Grid Cell {selection_id}: {area_label} - {units} per {time_type}</b>",
            'y': 0.92,
            'x': 0.48,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(
                family='Roboto',
                size=20
            ),
        }
        tick_format = ".2f"

    df['area_type'] = id_type

    # Construct figure object
    fig = px.line(df, x='Year', y='var', custom_data=['area_type'])
    fig.update_layout(
        title=title_text,
        margin=go.layout.Margin(
            l=30,  # left margin
            r=60,  # right margin
            b=70,  # bottom margin
            t=70  # top margin
        ),

    )

    # update x and y axis layout options
    fig.update_xaxes(nticks=nticks, title_text='Time')
    fig.update_yaxes(title_text=units, tickformat=tick_format)

    return fig


def get_target_years(start, end, options_list):
    """Return a string based list of the year range

       :param start:            Start Year
       :type start:             str

       :param end:              End year
       :type end:               str

       :param options_list      months from dropdown
       :type options_list       dict

       :return:                 list of years

    """
    return [i['value'] for i in options_list if i['value'] <= end]


def process_file(contents, filename, filedate, years, row_count="max"):
    """Process and decode uploaded file and the calculated units

    :param contents:             Raw contents of uploaded file
    :type contents:              str

    :param filename:             Name of uploaded file
    :type filename:              str

    :param filedate:             Date of uploaded file
    :type filedate:              str

    :param years:                List of years to process
    :type years:                 list

    :param row_count:            Row number to read from to reduce number of rows read in certain situations
    :type row_count:             int

    :return:                     Processed contents object and calculated unit type

    """

    # Pre-processing of years, columns, units, set up variables
    if years:
        read_cols = years + ['id']
    else:
        read_cols = "all"
    f = filename[0]
    split = f.split('_')

    # Process file contents based on extension
    try:
        if 'zip' in filename[0]:
            zip_file = None
            for content, name, date in zip(contents, filename, filedate):
                # the content needs to be split. It contains the type and the real content
                content_type, content_string = content.split(',')
                # Decode the base64 string
                content_decoded = base64.b64decode(content_string)
                # Use BytesIO to handle the decoded content
                zip_str = io.BytesIO(content_decoded)
                # Use ZipFile to take the BytesIO output
                zip_file = ZipFile(zip_str, 'r')
                filename = zip_file.namelist()[0]
            # Read file based on input parameters for number of rows/columns to help performance
            with zip_file.open(filename) as csvfile:
                if row_count == "max":
                    if read_cols == "all":
                        xanthos_data = pd.read_csv(csvfile, encoding='utf8', sep=",")
                    else:
                        xanthos_data = pd.read_csv(csvfile, encoding='utf8', sep=",", usecols=read_cols)
                else:
                    if read_cols == "all":
                        xanthos_data = pd.read_csv(csvfile, encoding='utf8', sep=",", nrows=row_count)
                    else:
                        xanthos_data = pd.read_csv(csvfile, encoding='utf8', sep=",", usecols=read_cols,
                                                   nrows=row_count)
        elif 'csv' in filename[0]:
            # Assume that the user uploaded a CSV file and decode
            content_type, content_string = contents[0].split(',')
            decoded = base64.b64decode(content_string)
            # Read file based on input parameters for number of rows/columns to help performance
            if row_count == "max":
                if read_cols == "all":
                    xanthos_data = pd.read_csv(io.StringIO(decoded.decode('utf-8')), error_bad_lines=False,
                                               warn_bad_lines=True)
                else:
                    xanthos_data = pd.read_csv(io.StringIO(decoded.decode('utf-8')), usecols=read_cols,
                                               error_bad_lines=False, warn_bad_lines=True)
            else:
                if read_cols == "all":
                    xanthos_data = pd.read_csv(io.StringIO(decoded.decode('utf-8')), nrows=row_count,
                                               error_bad_lines=False, warn_bad_lines=True)
                else:
                    xanthos_data = pd.read_csv(io.StringIO(decoded.decode('utf-8')), nrows=row_count, usecols=read_cols,
                                               error_bad_lines=False, warn_bad_lines=True)
    except Exception as e:
        print(e)
        return None
    return [xanthos_data, split]


def process_input_years(contents, filename, filedate):
    """Process just the first row of input file to get list of available years

    :param contents:             Raw contents of uploaded file
    :type contents:              str

    :param filename:             Name of uploaded file
    :type filename:              str

    :param filedate:             Date of uploaded file
    :type filedate:              str

    :return:                     Processed list of years available in file data

    """

    file_data = process_file(contents, filename, filedate, years=[], row_count=0)[0]
    target_years = get_available_years(file_data)
    return target_years


def hydro_area_lookup(area_id, df_ref, area_key):
    """Get max row in data file of a particular area's grid cells to reduce row count for performance

    :param area_id:                 ID of area to find it's grid cells
    :type area_id:              int

    :param df_ref:                  Reference dataframe
    :type df_ref:                   dataframe

    :area_key:                      Type of area (country or basin)
    :type area_key:                 str

    :return:                        int; Max row of area in file data

    """

    # get which grid cells are associated with the target basin
    target_idx_list = df_ref[df_ref[area_key] == area_id].copy()
    return max(target_idx_list['grid_id'])


def hydro_cell_lookup(cell_id, df_ref):
    """Get max row of a particular grid cell to reduce row count for performance

    :param cell_id:                 ID of cell
    :type cell_id:                  int

    :param df_ref:                  Reference dataframe
    :type df_ref:                   dataframe

    :return:                        int; Max row of cell in file data

    """

    # get which grid cells are associated with the target basin
    target_idx_list = df_ref[df_ref['grid_id'] == cell_id].copy()
    return max(target_idx_list['grid_id'])


def update_choro_select(df_ref, df_per_area, features, year_list, mapbox_token, selected_data, start, end,
                        statistic, file_info, months, area_type, units):
    """Return a choropleth figured object based off the area's within the selected region

    :param df_ref:                  Reference xanthos dataframe
    :type df_ref:                   dataframe

    :param df_per_area:             Processed data dataframe
    :type df_per_area:              dataframe

    :param features:                Reference geo dataframe
    :type features:                 dataframe

    :param year_list:               List of years to process
    :type year_list:                list

    :param mapbox_token:            Mapbox access token
    :type mapbox_token:             string

    :param selected_data:           Select event data for the choropleth graph
    :type selected_data:            dict

    :param start:                   Start year
    :type start:                    str

    :param end:                     End year
    :type end:                      str

    :param statistic:               Statistic to be computed
    :type statistic:                str

    :param units:                   Unit of measurement
    :type units:                    str

    :param file_info                Name of uploaded file
    :type file_info                 list

    :param months                   months from dropdown
    :type months                    list

    :param area_type                Type of area (country or basin)
    :type area_type                 str

    :return:                        Choropleth figure object

    """

    unit_type = get_unit_info(file_info)

    # Set up variables based on current area type selected
    if area_type == "gcam":
        area_name = "basin_name"
        area_id = "basin_id"
        feature_id = "properties.basin_id"
        area_loc = "basin_id"
        area_title = "Basin"
    else:
        area_name = "country_name"
        area_id = "country_id"
        feature_id = "properties.name"
        area_loc = "country_name"
        area_title = "Country"

    # Get selected area list based on area or grid cell, depending on selection data
    if 'cell_id' not in selected_data['points'][0]['customdata'].keys():
        area_id_list = [i['customdata'][area_loc] for i in selected_data['points']]
    else:
        area_id_list = [i['customdata'][0] for i in selected_data['points']]

    # Subset dataframes
    df_per_area = df_per_area[df_per_area[area_loc].isin(flatten(area_id_list))]
    subset = df_ref[df_ref[area_loc].isin(flatten(area_id_list))].copy()

    # Do some lat/lon calculations to try to find a midpoint of selection data
    lon_min = subset['longitude'].min()
    lon_max = subset['longitude'].max()
    lat_min = subset['latitude'].min()
    lat_max = subset['latitude'].max()
    lon = (lon_min + lon_max) / 2
    lat = (lat_min + lat_max) / 2

    # Build custom data list objects for each item
    custom_data = [{'basin_id': x, 'country_id': y, 'country_name': z} for x, y, z in
                   zip(df_per_area['basin_id'], df_per_area['country_id'], df_per_area['country_name'])]
    # Plot figure
    fig = go.Figure(go.Choroplethmapbox(geojson=features, locations=df_per_area[area_loc],
                                        z=df_per_area['var'].astype(str), marker=dict(opacity=0.7),
                                        text=df_per_area.apply(lambda row: f"<b>{row[area_name]}</b><br>"
                                                                           f"ID: {row[area_id]}<br><br>"
                                                                           f"{unit_type} ({units}): {row['var']}"
                                                                           f" ({statistic})",
                                                               axis=1), colorscale="Plasma",
                                        featureidkey=feature_id, legendgroup=unit_type,
                                        hoverinfo="text",
                                        colorbar={'separatethousands': True, 'tickformat': ",",
                                                  'title': unit_type + ' (' + units + ')'},
                                        customdata=custom_data))

    # Update figure layout options
    fig.update_layout(
        title={
            'text': f"<b>{unit_type} ({statistic}) by {area_title} {start if len(start) <= 4 else start[0:4] + '-' + start[4:6]} - "
                    f"{end if len(end) <= 4 else end[0:4] + '-' + end[4:6]}</b>",
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
        mapbox_accesstoken=mapbox_token, mapbox={'center': {'lat': lat, 'lon': lon}, 'zoom': 3}
    )

    return fig


def update_choro_grid(df_ref, df, basin_features, year_list, mapbox_token, selected_data, start, end, statistic,
                      file_info,
                      months, area_type, units, filename):
    """Return a scattermapbox figure object for viewing by grid cell

    :param df_ref:                      Xanthos reference dataframe
    :type df_ref:                       dataframe

    :param df:                          Processed data dataframe
    :type df:                           dataframe

    :param basin_features:              geo reference dataframe
    :type basin_features:               dataframe

    :param year_list:                   List of years to process
    :type year_list:                    list

    :param mapbox_token:                Mapbox access token
    :type mapbox_token:                 string

    :param selected_data:               Select event data for the choropleth graph
    :type selected_data:                dict

    :param start:                       Start year
    :type start:                        str

    :param end:                         End year
    :type end:                          str

    :param statistic:                   Statistic to be computed
    :type statistic:                    str

    :param file_info                    Name of uploaded file
    :type file_info                     list

    :param units:                       Unit of measurement
    :type units:                        str

    :param months                       months from dropdown
    :type months                        list

    :param area_type                    Type of area (country or basin)
    :type area_type                     str

    :param filename                     Name of uploaded file
    :type filename                      list

    :return:                            Scattermapbox figure object

    """

    # Get chose units information
    unit_type = get_unit_info(file_info)
    unit_from_file = get_units_from_name(filename)

    # Set up area specific variables
    if area_type == "gcam":
        area_name = "basin_name"
        area_id = "basin_id"
        feature_id = "properties.basin_id"
        area_loc = "basin_id"
        area_title = "Basin"
    else:
        area_name = "country_name"
        area_id = "country_id"
        feature_id = "properties.name"
        area_loc = "country_name"
        area_title = "Country"

    # Load all data if the user selects nothing
    if selected_data is None:
        df_selected = data_per_cell(df, statistic, year_list, df_ref, months, area_type, unit_from_file, units)
    else:
        # Set up variables for selection by box tool if 'range' is in the selected data
        if 'range' in selected_data.keys():
            area_id_list = [i['customdata'][area_loc] for i in selected_data['points']]
            df = df[df[area_loc].isin(flatten(area_id_list))]
            df_selected = data_per_cell(df, statistic, year_list, df_ref, months, area_type, unit_from_file, units)
            selected_range = selected_data['range']['mapbox']
            min_lon = min((selected_range[0][0], selected_range[1][0]))
            max_lon = max((selected_range[0][0], selected_range[1][0]))
            min_lat = min((selected_range[0][1], selected_range[1][1]))
            max_lat = max((selected_range[0][1], selected_range[1][1]))
        # Set up variables for selection by lasso tool
        else:
            selected_range = selected_data['lassoPoints']['mapbox']
            min_lon = min(x[0] for x in selected_range)
            max_lon = max(x[0] for x in selected_range)
            min_lat = min(x[1] for x in selected_range)
            max_lat = max(x[1] for x in selected_range)
            # Build selected items list depending on view options
            if 'cell_id' not in selected_data['points'][0]['customdata'].keys():
                area_id_list = [i['customdata'][area_loc] for i in selected_data['points']]
                df = df[df[area_loc].isin(flatten(area_id_list))]
                df_selected = data_per_cell(df, statistic, year_list, df_ref, months, area_type, unit_from_file, units)
            else:
                df_selected = data_per_cell(df, statistic, year_list, df_ref, months, area_type, unit_from_file, units)
                selected_points = [i['customdata']['cell_id'] for i in selected_data['points']]
                df_selected = df_selected[df_selected['id'].isin(flatten(selected_points))]

    df_selected['var'] = round(df_selected['var'], 2)
    lon_min = df_selected['longitude'].min()
    lon_max = df_selected['longitude'].max()
    lat_min = df_selected['latitude'].min()
    lat_max = df_selected['latitude'].max()
    lon = (lon_min + lon_max) / 2
    lat = (lat_min + lat_max) / 2

    # Build custom data list for storing at each point/item in graph
    custom_data = [{'basin_id': x, 'country_id': y, 'country_name': z, 'cell_id': c} for x, y, z, c in
                   zip(df_selected['basin_id'], df_selected['country_id'], df_selected['country_name'],
                       df_selected['id'])]

    fig = go.Figure(go.Scattermapbox(lat=df_selected['latitude'], lon=df_selected['longitude'],
                                     mode='markers', customdata=custom_data,
                                     text=df_selected.apply(lambda row: f"<b>{row[area_name]}</b><br>"
                                                                        f"ID: {row[area_id]}<br>"
                                                                        f"Grid Cell: {row['id']}<br><br>"
                                                                        f"{unit_type} ({units}): {row['var']} "
                                                                        f"({statistic})",
                                                            axis=1), hoverinfo="text",

                                     marker=go.scattermapbox.Marker(
                                         size=11,
                                         color=df_selected['var'],
                                         opacity=0.4,
                                         showscale=True,
                                         colorbar={'title': unit_type + '(' + units + ')'}
                                     )
                                     ))
    # update layout options
    fig.update_layout(
        title={
            'text': f"<b>{unit_type} ({statistic}) by {area_title} {start if len(start) <= 4 else start[0:4] + '-' + start[4:6]} - "
                    f"{end if len(end) <= 4 else end[0:4] + '-' + end[4:6]}</b>",
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
        mapbox_accesstoken=mapbox_token, mapbox={'center': {'lat': lat, 'lon': lon}, 'zoom': 3}
    )

    return fig


def flatten(x):
    """Flatten an iterable

        :param x:                     Object to be flattened
        :type x:                      *

        :return:                      Flattened object, or original if unable to flatten

        """

    if isinstance(x, collections.Iterable) and not isinstance(x, str):
        return [a for i in x for a in flatten(i)]
    else:
        return [x]
