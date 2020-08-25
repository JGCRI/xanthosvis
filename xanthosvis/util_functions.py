import base64
import io
import json
from zipfile import ZipFile

import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import datetime
import numpy as np


def get_available_years(in_file, non_year_fields=None):
    """Get available years from file.  Reads only the header from the file.

    :params in_file:               Processed file as a dataframe
    :type in_file:                 dataframe

    :param non_year_fields:        list of non-year fields to drop from the file
    :type non_year_fields:         list

    :return:                       list of available years as integers

    """

    # drop non-year fields
    if non_year_fields is None:
        non_year_fields = ['id']
    in_file.drop(columns=non_year_fields, inplace=True)
    year_list = list()
    year_list = [{'label': i if len(i) == 4 else i[0:4] + '-' + i[4:6], 'value': i} for i in in_file.columns]
    month_list = list()
    if len(in_file.columns[0]) == 6:
        month_list = np.unique([i[4:6] for i in in_file.columns])
    else:
        month_list = None
    return year_list, month_list


def get_available_months(months_list):
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
    """Return a list of available through years that are >= the start year.

    :param available_year_list:            List of available years from the input file
    :type available_year_list:             list

    :param start_year:                     start year
    :type start_year:                      int

    :return:                               list of available through years

    """

    # Construct options for drop down based on input parameters
    options = []
    for i in available_year_list:
        if int(i['value']) >= int(start_year):
            options.append(i)
    return options


def basin_to_gridcell_dict(df_reference):
    """Generate a dictionary of gridcell id to basin id {grid_id: basin_id}

    :param df_reference:            Input data reference dataframe
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

    :param df_reference:            Input data reference dataframe
    :type df_reference:             dataframe

    :return:                        dict. {grid_id: basin_id}

    """

    # select target fields
    df_reference = df_reference[['grid_id', 'basin_id']]

    # set index that will become dictionary key
    df_reference.set_index('grid_id', inplace=True)

    return df_reference.to_dict()['basin_id']


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

    # add basin id
    df['basin_id'] = df['id'].map(grid_basin_dict)

    return df


def data_per_basin(df, statistic, yr_list, df_ref, months):
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

    :return:                        dataframe; grouped by basin for statistic

    """

    if months is not None and len(months) > 0:
        yr_list = [c for c in yr_list if c[4:6] in months]
    #     df = df.drop(axis=1,[if i[4:6] in months for i in df.columns] ) #np.unique([i[4:6] for i in df.columns])
    #     [x for x in df.columns[df.columns.str.contains()]]
    #     df.filter(regex='^201')
    #     cols = [c for c in df.columns if c[4:6] not in months]
    #
    #     df = df[cols]

    # sum data by basin by year
    grp = df.groupby('basin_id').sum()

    grp.drop(columns=['id'], inplace=True)

    # calculate stat
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

    # Map basin values using df_ref
    grp.reset_index(inplace=True)
    mapping = dict(df_ref[['basin_id', 'basin_name']].values)
    grp['basin_name'] = grp.basin_id.map(mapping)

    return grp


def data_per_cell(df, statistic, yr_list, df_ref, months):
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

    :return:                        dataframe; grouped by basin for statistic

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

    # grp.drop(columns=yr_list, inplace=True)

    # grp.reset_index(inplace=True)
    # mapping = dict(df_ref[['basin_id', 'basin_name']].values)
    # grp['basin_name'] = grp.basin_id.map(mapping)

    return df


def data_per_country(df, statistic, yr_list, df_ref, months):
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

    :return:                        dataframe; grouped by basin for statistic

    """

    if months is not None and len(months) > 0:
        yr_list = [c for c in yr_list if c[4:6] in months]
    #     df = df.drop(axis=1,[if i[4:6] in months for i in df.columns] ) #np.unique([i[4:6] for i in df.columns])
    #     [x for x in df.columns[df.columns.str.contains()]]
    #     df.filter(regex='^201')
    #     cols = [c for c in df.columns if c[4:6] not in months]
    #
    #     df = df[cols]

    # sum data by basin by year
    grp = df.groupby('basin_id').sum()

    grp.drop(columns=['id'], inplace=True)

    # calculate stat
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

    # Map basin values using df_ref
    grp.reset_index(inplace=True)
    mapping = dict(df_ref[['basin_id', 'basin_name']].values)
    grp['basin_name'] = grp.basin_id.map(mapping)

    return grp


def data_per_year_basin(df, basin_id, yr_list, months):
    """Generate a data frame representing the sum of the data per year for a target basin.

    :param df:                      input data having data per year
    :type df:                       dataframe

    :param basin_id:                id of basin to filter and aggregate data for
    :type basin_id:                 int

    :param yr_list                  list of years to consider
    :type yr_list                   list

    :return:                        dataframe; sum values per year for a target basin

    """

    if months is not None and len(months) > 0:
        yr_list = [c for c in yr_list if c[4:6] in months]

    # Sum data by basin by year
    grp = df.groupby('basin_id').sum()

    keep_cols = yr_list

    # Adjust columns and reset index
    grp.drop(columns=['id'], inplace=True)
    grp = grp[keep_cols]
    grp.reset_index(inplace=True)

    # Get only target basin_id
    dfx = grp.loc[grp['basin_id'] == basin_id].copy()

    # Adjust return DF columns and reset index
    dfx.drop(columns=['basin_id'], inplace=True)
    df = dfx.T.copy()
    df.reset_index(inplace=True)
    df.columns = ['Year', 'var']

    return df


def data_per_year_cell(df, cell_id, yr_list, months):
    """Generate a data frame representing the sum of the data per year for a target basin.

    :param df:                      input data having data per year
    :type df:                       dataframe

    :param cell_id:                id of basin to filter and aggregate data for
    :type cell_id:                 int

    :param yr_list                  list of years to consider
    :type yr_list                   list

    :return:                        dataframe; sum values per year for a target basin

    """

    # Sum data by basin by year
    # grp = df.groupby('basin_id').sum()

    if months is not None and len(months) > 0:
        yr_list = [c for c in yr_list if c[4:6] in months]

    keep_cols = yr_list

    # Adjust columns and reset index
    # grp.drop(columns=['id'], inplace=True)
    # grp = grp[keep_cols]
    # grp.reset_index(inplace=True)

    # Get only target basin_id
    # dfx = grp.loc[grp['basin_id'] == cell_id].copy()

    # Adjust return DF columns and reset index
    # dfx.drop(columns=['basin_id'], inplace=True)
    # df = dfx.T.copy()
    # df.reset_index(inplace=True)
    df = df[df['id'] == cell_id].copy()
    df.drop(columns=['basin_id', 'id'], inplace=True)
    df = df[keep_cols]
    df = df.T.copy()
    df.reset_index(inplace=True)
    df.columns = ['Year', 'var']

    return df


def process_geojson(in_file):
    """Read in geojson spatial data and add in a feature level id.

    :param in_file:                 Full path with file name and extension to the input geojson file
    :type in_file:                  str

    :return:                        geojson array

    """

    with open(in_file) as get:
        basin_features = json.load(get)

    for fx in basin_features['features']:
        fx['id'] = fx['properties']['basin_id']

    return basin_features


def get_unit_info(units):
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
    if len(units) > 1:
        if units[1] == "km3peryear":
            unit_type = "km³/y"
        elif units[1] == "km3permonth":
            unit_type = "km³/m"
        elif units[1] == "m3persec":
            unit_type = "m³/s"
        else:
            unit_type = "unknown"
    else:
        unit_type = "unknown"

    return [data_type, unit_type]


def plot_geo_choropleth(df_per_country, country_features, mapbox_token, statistic, start, end, units):
    unit_labels = get_unit_info(units)
    unit_type = unit_labels[0]
    unit_display = unit_labels[1]

    fig = go.Figure(go.Choroplethmapbox(geojson=country_features, locations=df_per_country.basin_id,
                                        z=df_per_country['var'].astype(str), marker=dict(opacity=0.7),
                                        text=df_per_country.apply(lambda row: f"<b>{row['basin_name']}</b><br>"
                                                                            f"ID: {row['basin_id']}<br><br>"
                                                                            f"{unit_type} ({unit_display}): {row['var']} "
                                                                            f"({statistic})",
                                                                  axis=1), colorscale="Plasma",
                                        featureidkey="properties.basin_id", legendgroup="Runoff",
                                        hoverinfo="text",
                                        colorbar={'separatethousands': True, 'tickformat': ",",
                                                  'title': unit_type + ' ' + '(' + unit_display + ')'},
                                        customdata=df_per_country['basin_id']))

    fig.update_layout(
        title={
            'text': f"<b>{unit_type} ({statistic}) by Basin {start if len(start) <= 4 else start[0:4] + '-' + start[4:6]} - "
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

def plot_choropleth(df_per_basin, basin_features, mapbox_token, statistic, start, end, units):
    """Plot interactive choropleth map for basin level statistics.

    :param df_per_basin:            dataframe with basin level stats
    :type df_per_basin:             dataframe

    :param basin_features:          geojson spatial data and basin id field
    :type basin_features:           dataframe

    :param mapbox_token             Access token for mapbox
    :type mapbox_token              str

    :param statistic                Chosen statistic to run on data
    :type statistic                 str

    :param start                    beginning year
    :type start                     number

    :param end                      ending year
    :type end                       number

    :param units:               Unit of measurement
    :type units:                str

    """

    unit_labels = get_unit_info(units)
    unit_type = unit_labels[0]
    unit_display = unit_labels[1]

    fig = go.Figure(go.Choroplethmapbox(geojson=basin_features, locations=df_per_basin.basin_id,
                                        z=df_per_basin['var'].astype(str), marker=dict(opacity=0.7),
                                        text=df_per_basin.apply(lambda row: f"<b>{row['basin_name']}</b><br>"
                                                                            f"ID: {row['basin_id']}<br><br>"
                                                                            f"{unit_type} ({unit_display}): {row['var']} "
                                                                            f"({statistic})",
                                                                axis=1), colorscale="Plasma",
                                        featureidkey="properties.basin_id", legendgroup="Runoff",
                                        hoverinfo="text",
                                        colorbar={'separatethousands': True, 'tickformat': ",",
                                                  'title': unit_type + ' ' + '(' + unit_display + ')'},
                                        customdata=df_per_basin['basin_id']))

    fig.update_layout(
        title={
            'text': f"<b>{unit_type} ({statistic}) by Basin {start if len(start) <= 4 else start[0:4] + '-' + start[4:6]} - "
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


def plot_hydrograph(df, selection_id, df_ref, id_type, units):
    """Plot a hydrograph of a specific basin.

    :param df:                   Input dataframe with data and basin id for a target basin
    :type df:                    dataframe

    :param selection_id:                  cell or basin id
    :type selection_id:                   int

    :param df_ref:              Reference dataframe with gis data
    :type df_ref                dataframe

    :param id_type:              Type of ID passed, basin or cell
    :type id_type                str

    """
    unit_labels = get_unit_info(units)
    unit_type = unit_labels[0]
    unit_display = unit_labels[1]

    # Process dataframe and set up variables
    df['var'] = round(df['var'], 2)
    title_text = ""
    tick_format = ""
    if len(df['Year'][0]) > 4:
        df['Year'] = [datetime.datetime.strptime(i, "%Y%m") for i in df['Year']]
        time_type = 'Month'
    else:
        time_type = 'Year'
    nticks = len(df)
    if nticks > 40:
        nticks = 40

    if id_type == 'basin':
        df_basin = df_ref[df_ref['basin_id'] == selection_id][0:1]
        df_basin = df_basin['basin_name']
        basin_name = df_basin.iat[0]
        title_text = {
            'text': f"<b>Basin {selection_id}: {basin_name} - {unit_type} per {time_type}</b>",
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
    elif id_type == 'cell':
        basin_name = df_ref[df_ref['grid_id'] == selection_id]['basin_name'].iat[0]
        title_text = {
            'text': f"<b>Grid Cell {selection_id}: {basin_name} - {unit_type} per {time_type}</b>",
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

    # Construct figure object
    fig = px.line(df, x='Year', y='var', title=f"Basin {selection_id} {unit_type} per {time_type}")
    fig.update_layout(
        title=title_text,
        margin=go.layout.Margin(
            l=30,  # left margin
            r=60,  # right margin
            b=70,  # bottom margin
            t=70  # top margin
        ),

    )

    fig.update_xaxes(nticks=nticks, title_text='Time')
    fig.update_yaxes(title_text=unit_display, tickformat=tick_format)
    # fig.update_layout(yaxis_tickformat=',')
    return fig


def get_target_years(start, end, options_list):
    """Return a string based list of the year range

       :param start:            Start Year
       :type start:             str

       :param end:              End year
       :type end:               str

       :return:                 list of years

    """
    return [i['value'] for i in options_list if i['value'] <= end]


def process_file(contents, filename, filedate, years, row_count="max"):
    """Return processed and decoded object for the uploaded file and the calculated units

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

    # Try catch to process file based on type
    try:
        if 'zip' in filename[0]:
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
    """Process input file to get list of available years from it

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


def hydro_basin_lookup(basin_id, df_ref):
    """Get max row of a particular basin's grid cells to reduce row count for performance

    :param basin_id:             ID of basin to find it's grid cells
    :type basin_id:              int

    :param df_ref:               Reference dataframe
    :type df_ref:                dataframe

    :return:                     Max row of basin in file data

    """

    # get which grid cells are associated with the target basin
    target_idx_list = df_ref[df_ref['basin_id'] == basin_id].copy()
    return max(target_idx_list['grid_id'])


def hydro_cell_lookup(cell_id, df_ref):
    """Get max row of a particular basin's grid cells to reduce row count for performance

    :param cell_id:             ID of cell
    :type cell_id:              int

    :param df_ref:               Reference dataframe
    :type df_ref:                dataframe

    :return:                     Max row of cell in file data

    """

    # get which grid cells are associated with the target basin
    target_idx_list = df_ref[df_ref['grid_id'] == cell_id].copy()
    return max(target_idx_list['grid_id'])


def update_choro_click(df_ref, df_per_basin, basin_features, mapbox_token, graph_click, start, end, statistic, units):
    """Return a choropleth figured object based off user click event

    :param df_ref:                   Reference dataframe
    :type df_ref:                    dataframe

    :param df_per_basin:             Processed data dataframe
    :type df_per_basin:              dataframe

    :param basin_features:           Basin features reference
    :type basin_features:            dataframe

    :param mapbox_token:             Mapbox access token
    :type mapbox_token:              string

    :param graph_click:              Click event data for the choropleth graph
    :type graph_click:               dict

    :param start:                    Start year
    :type start:                     int

    :param end:                      End year
    :type end:                       int

    :param statistic:                Statistic to be computed
    :type statistic:                 str

    :param units:               Unit of measurement
    :type units:                str

    :return:                         Choropleth figure object

    """

    basin_id = graph_click['points'][0]['customdata'][0]
    subset = df_ref[df_ref['basin_id'] == basin_id].copy()
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
    fig = go.Figure(go.Choroplethmapbox(geojson=basin_features, locations=df_per_basin.basin_id,
                                        z=df_per_basin['Runoff (km³)'].astype(str), marker=dict(opacity=0.7),
                                        text=df_per_basin.apply(lambda row: f"<b>{row['basin_name']}</b><br>"
                                                                            f"ID: {row['basin_id']}<br><br>"
                                                                            f"Runoff (km³): {row['Runoff (km³)']} "
                                                                            f"({statistic})",
                                                                axis=1), colorscale="Plasma",
                                        featureidkey="properties.basin_id", legendgroup="Runoff",
                                        hoverinfo="text",
                                        colorbar={'separatethousands': True, 'tickformat': ",",
                                                  'title': 'Runoff (km³)',
                                                  'tickvals': [0, 500, 1000, 1500, 2000, 4000]},
                                        customdata=[df_per_basin['basin_id'], df_per_basin['id']]))

    fig.update_layout(
        title={
            'text': f"<b>Runoff ({statistic}) by Basin {start if len(start) <= 4 else start[0:4] + '-' + start[4:6]} - "
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


def update_choro_select(df_ref, df_per_basin, basin_features, year_list, mapbox_token, selected_data, start, end,
                        statistic, units):
    """Return a choropleth figured object based off user area select event

    :param df_ref:                  Reference dataframe
    :type df_ref:                   dataframe

    :param df_per_basin:                      Processed data dataframe
    :type df_per_basin:                       dataframe

    :param basin_features:                      Reference dataframe
    :type basin_features:                       dataframe

    :param year_list:               List of years to process
    :type year_list:                list

    :param mapbox_token:            Mapbox access token
    :type mapbox_token:             string

    :param selected_data:           Select event data for the choropleth graph
    :type selected_data:            dict

    :param start:                   Start year
    :type start:                    int

    :param end:                     End year
    :type end:                      int

    :param statistic:               Statistic to be computed
    :type statistic:                str

    :param units:               Unit of measurement
    :type units:                str

    :return:                        Choropleth figure object

    """

    unit_labels = get_unit_info(units)
    unit_type = unit_labels[0]
    unit_display = unit_labels[1]

    if selected_data['points'][0]['customdata'].__class__ == int:
        basin_id = [i['customdata'] for i in selected_data['points']]
    else:
        basin_id = [i['customdata'][0] for i in selected_data['points']]
    df_per_basin = df_per_basin[df_per_basin['basin_id'].isin(basin_id)]
    subset = df_ref[df_ref['basin_id'].isin(basin_id)].copy()
    lon_min = subset['longitude'].min()
    lon_max = subset['longitude'].max()
    lat_min = subset['latitude'].min()
    lat_max = subset['latitude'].max()
    lon = (lon_min + lon_max) / 2
    lat = (lat_min + lat_max) / 2
    # custom_data = [[x, y] for x, y in zip(df_per_basin['basin_id'], df_per_basin['id'])]
    fig = go.Figure(go.Choroplethmapbox(geojson=basin_features, locations=df_per_basin.basin_id,
                                        z=df_per_basin['var'].astype(str), marker=dict(opacity=0.7),
                                        text=df_per_basin.apply(lambda row: f"<b>{row['basin_name']}</b><br>"
                                                                            f"ID: {row['basin_id']}<br><br>"
                                                                            f"{unit_type} ({unit_display}): {row['var']} "
                                                                            f"({statistic})",
                                                                axis=1), colorscale="Plasma",
                                        featureidkey="properties.basin_id", legendgroup=unit_type,
                                        hoverinfo="text",
                                        colorbar={'separatethousands': True, 'tickformat': ",",
                                                  'title': unit_type + ' (' + unit_display + ')'},
                                        customdata=df_per_basin['basin_id']))

    fig.update_layout(
        title={
            'text': f"<b>{unit_type} ({statistic}) by Basin {start if len(start) <= 4 else start[0:4] + '-' + start[4:6]} - "
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


def update_choro_grid(df_ref, df, basin_features, year_list, mapbox_token, selected_data, start, end, statistic, units,
                      months):
    """Return a choropleth figured object based off user area select event

    :param df_ref:                  Reference dataframe
    :type df_ref:                   dataframe

    :param df:                      Processed data dataframe
    :type df:                       dataframe

    :param basin_features:                      Reference dataframe
    :type basin_features:                       dataframe

    :param year_list:               List of years to process
    :type year_list:                list

    :param mapbox_token:            Mapbox access token
    :type mapbox_token:             string

    :param selected_data:           Select event data for the choropleth graph
    :type selected_data:            dict

    :param start:                   Start year
    :type start:                    int

    :param end:                     End year
    :type end:                      int

    :param statistic:               Statistic to be computed
    :type statistic:                str

    :param units:               Unit of measurement
    :type units:                str

    :return:                        Choropleth figure object

    """

    unit_labels = get_unit_info(units)
    unit_type = unit_labels[0]
    unit_display = unit_labels[1]

    if selected_data is None:
        df_selected = data_per_cell(df, statistic, year_list, df_ref, months)

    else:
        if 'range' in selected_data.keys():
            if selected_data['points'][0]['customdata'].__class__ == int:
                basin_id = [i['customdata'] for i in selected_data['points']]
            else:
                basin_id = [i['customdata'][0] for i in selected_data['points']]
            df = df[df['basin_id'].isin(basin_id)]
            df_selected = data_per_cell(df, statistic, year_list, df_ref, months)
            selected_range = selected_data['range']['mapbox']
            min_lon = min((selected_range[0][0], selected_range[1][0]))
            max_lon = max((selected_range[0][0], selected_range[1][0]))
            min_lat = min((selected_range[0][1], selected_range[1][1]))
            max_lat = max((selected_range[0][1], selected_range[1][1]))
        else:
            selected_range = selected_data['lassoPoints']['mapbox']
            min_lon = min(x[0] for x in selected_range)
            max_lon = max(x[0] for x in selected_range)
            min_lat = min(x[1] for x in selected_range)
            max_lat = max(x[1] for x in selected_range)
            if selected_data['points'][0]['customdata'].__class__ == int:
                basin_id = [i['customdata'] for i in selected_data['points']]
                df = df[df['basin_id'].isin(basin_id)]
                df_selected = data_per_cell(df, statistic, year_list, df_ref)
            else:
                df_selected = data_per_cell(df, statistic, year_list, df_ref)
                selected_points = [i['customdata'][1] for i in selected_data['points']]
                df_selected = df_selected[df_selected['id'].isin(selected_points)]

    df_selected['var'] = round(df_selected['var'], 2)
    lon_min = df_selected['longitude'].min()
    lon_max = df_selected['longitude'].max()
    lat_min = df_selected['latitude'].min()
    lat_max = df_selected['latitude'].max()
    lon = (lon_min + lon_max) / 2
    lat = (lat_min + lat_max) / 2
    # df_per_basin = xvu.data_per_cell(df, statistic, year_list, df_ref_sub)

    # fig = go.Figure(go.Densitymapbox(lat=df_selected['latitude'], lon=df_selected['longitude'],
    #                                  z=df_selected['Runoff (km³)'], radius=10))
    # fig = go.Figure()
    # fig.add_trace(go.Scattermapbox(lat=df_selected['latitude'], lon=df_selected['longitude'],
    #                                mode='markers', customdata=np.dstack((df_selected['basin_id'], df_selected['id'])),
    #                                text=df_selected.apply(lambda row: f"<b>{row['basin_name']}</b><br>"
    #                                                                   f"ID: {row['basin_id']}<br>"
    #                                                                   f"Grid Cell: {row['id']}<br><br>"
    #                                                                   f"Runoff (km³): {row['Runoff (km³)']} "
    #                                                                   f"({statistic})",
    #                                                       axis=1), hoverinfo="text",
    #                                # colorbar={'title': 'Runoff (km³)'},
    #                                marker=go.scattermapbox.Marker(
    #                                    size=14,
    #                                    color=df_selected['Runoff (km³)'],
    #                                    opacity=0.4,
    #                                    showscale=True
    #                                )
    #                                ))
    custom_data = [[x, y] for x, y in zip(df_selected['basin_id'], df_selected['id'])]
    fig = go.Figure(go.Scattermapbox(lat=df_selected['latitude'], lon=df_selected['longitude'],
                                     mode='markers', customdata=custom_data,
                                     text=df_selected.apply(lambda row: f"<b>{row['basin_name']}</b><br>"
                                                                        f"ID: {row['basin_id']}<br>"
                                                                        f"Grid Cell: {row['id']}<br><br>"
                                                                        f"{unit_type} ({unit_display}): {row['var']} "
                                                                        f"({statistic})",
                                                            axis=1), hoverinfo="text",

                                     marker=go.scattermapbox.Marker(
                                         size=14,
                                         color=df_selected['var'],
                                         opacity=0.4,
                                         showscale=True,
                                         colorbar={'title': unit_type + '(' + unit_display + ')'}
                                     )
                                     ))
    fig.update_layout(
        title={
            'text': f"<b>{unit_type} ({statistic}) by Basin {start if len(start) <= 4 else start[0:4] + '-' + start[4:6]} - "
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
