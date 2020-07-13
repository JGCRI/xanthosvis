import base64
import io
from zipfile import ZipFile
import plotly.graph_objs as go
import pandas as pd
import plotly.express as px
import json


def get_available_years(in_file, non_year_fields=['id']):
    """Get available years from file.  Reads only the header from the file.

    :params in_file:               Processed file as a dataframe
    :type in_file:                 dataframe

    :param non_year_fields:        list of non-year fields to drop from the file
    :type non_year_fields:         list

    :return:                       list of available years as integers

    """

    # drop non-year fields
    in_file.drop(columns=non_year_fields, inplace=True)

    return [{'label': i, 'value': i} for i in in_file.columns]


def available_through_years(available_year_list, start_year):
    """Return a list of available through years that are >= the start year.

    :param available_year_list:            List of available years from the input file
    :type available_year_list:             list

    :param start_year:                     start year
    :type start_year:                      int

    :return:                               list of available through years

    """
    options = []
    for i in available_year_list:
        if int(i['value']) >= int(start_year):
            options.append(i)
    return options
    # return [i for i in available_year_list if i >= start_year]


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


def prepare_data(df, df_ref):
    """Read in data from input file and add the basin id from a reference file.

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


def data_per_basin(df, statistic, yr_list, df_ref):
    """Generate a data frame representing data per basin for all years
    represented by an input statistic.

    :param df:                      Data with basin id
    :type df:                       dataframe

    :param statistic:               statistic name from user input
    :type statistic:                str

    :param yr_list:                 List of years to process
    :type yr_list:                  list

    :return:                        dataframe; grouped by basin for statistic

    """

    # sum data by basin by year
    grp = df.groupby('basin_id').sum()

    grp.drop(columns=['id'], inplace=True)

    # calculate stat
    if statistic == 'mean':
        grp['q'] = grp[yr_list].mean(axis=1)

    elif statistic == 'median':
        grp['q'] = grp[yr_list].median(axis=1)

    elif statistic == 'min':
        grp['q'] = grp[yr_list].min(axis=1)

    elif statistic == 'max':
        grp['q'] = grp[yr_list].max(axis=1)

    elif statistic == 'standard deviation':
        grp['q'] = grp[yr_list].std(axis=1)

    else:
        msg = f"The statistic requested '{statistic}' is not a valid option."
        raise ValueError(msg)

    grp.drop(columns=yr_list, inplace=True)

    grp.reset_index(inplace=True)
    mapping = dict(df_ref[['basin_id', 'basin_name']].values)
    grp['basin_name'] = grp.basin_id.map(mapping)

    return grp


def data_per_year_basin(df, basin_id, yr_list):
    """Generate a data frame representing the sum of the data per year for a target basin.

    :param df:                      input data having data per year
    :type df:                       dataframe

    :param basin_id:                id of basin to filter and aggregate data for
    :type basin_id:                 int

    :param yr_list                  list of years to consider
    :type yr_list                   list

    :return:                        dataframe; sum values per year for a target basin

    """

    # sum data by basin by year
    grp = df.groupby('basin_id').sum()

    keep_cols = yr_list

    grp.drop(columns=['id'], inplace=True)
    grp = grp[keep_cols]
    grp.reset_index(inplace=True)

    # get only target basin_id
    dfx = grp.loc[grp['basin_id'] == basin_id].copy()

    dfx.drop(columns=['basin_id'], inplace=True)

    df = dfx.T.copy()

    df.reset_index(inplace=True)

    df.columns = ['Year', 'q']

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


def plot_choropleth(df_per_basin, basin_features, start, end):
    """Plot interactive choropleth map for basin level statistics.

    :param df:                      dataframe with basin level stats
    :type df:                       dataframe

    :param geojson_basin:           geojson spatial data and basin id field
    :type geojson_basin:

    """
    fig = px.choropleth_mapbox(df_per_basin, geojson=basin_features, locations='basin_id',
                               featureidkey='properties.basin_id',
                               color='q', color_continuous_scale="Viridis", zoom=1, opacity=0.7)
    fig.update_layout(
        title={
            'text': f"Runoff by Basin {start} - {end}",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        xaxis_title="Lon",
        yaxis_title="Lat",
    )
    fig.update_layout(mapbox_style="carto-positron", mapbox_layers=[
        {
            "below": 'traces',
            "sourcetype": "raster",
            "source": [
                "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
            ]
        }
    ])

    return fig


def plot_hydrograph(df, basin_id, df_ref):
    """Plot a hydrograph of a specific basin.

    :param df:                   Input dataframe with data and basin id for a target basin
    :type df:                    dataframe

    :param basin_id:             basin id
    :type basin_id:              int

    """

    df['q'] = round(df['q'], 2)
    df['Runoff'] = df['q']
    df_basin = df_ref[df_ref['basin_id'] == basin_id][0:1]
    df_basin = df_basin['basin_name']
    basin_name = df_basin.iat[0]
    fig = px.line(df, x='Year', y='Runoff', title=f"Basin {basin_id} Runoff per Year")
    fig.update_layout(
        title={
            'text': f"<b>Basin {basin_id}: {basin_name} - Runoff per Year</b>",
            'y': 0.92,
            'x': 0.48,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(
                family='Roboto',
                size=20
            ),
        },
        margin=go.layout.Margin(
            l=30,  # left margin
            r=60,  # right margin
            b=70,  # bottom margin
            t=70  # top margin
        ),

    )
    fig.update_xaxes(title_text='Year')
    fig.update_yaxes(title_text='km³/yr')
    # fig.show()
    return fig


def get_target_years(start, end):
    return [str(i) for i in range(int(start), int(end) + 1)]


def process_file(contents, filename, filedate, years, row_count="max"):
    if years != 0:
        read_cols = years + ['id']
    else:
        read_cols = "all"
    f = filename[0]
    split = f.split('_')
    units = ""
    if len(split) > 1:
        units = split[1]
    else:
        unit_display = "km^3/yr"
    if units == 'km3peryear':
        unit_display = 'Km^3/yr'
    try:
        if 'zip' in filename[0]:
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

        elif 'xls' in filename[0]:
            # Assume that the user uploaded an excel file
            content_type, content_string = contents[0].split(',')
            decoded = base64.b64decode(content_string)
            if row_count == "max":
                if read_cols == "all":
                    xanthos_data = pd.read_excel(io.BytesIO(decoded))
                else:
                    xanthos_data = pd.read_excel(io.BytesIO(decoded), usecols=read_cols)
            else:
                if read_cols == "all":
                    xanthos_data = pd.read_excel(io.BytesIO(decoded), nrows=row_count)
                else:
                    xanthos_data = pd.read_excel(io.BytesIO(decoded), nrows=row_count, usecols=read_cols)
        elif 'csv' in filename[0]:
            # Assume that the user uploaded a CSV file
            content_type, content_string = contents[0].split(',')
            decoded = base64.b64decode(content_string)
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
        elif 'txt' in filename[0]:
            # Assume that the user uploaded a CSV file
            content_string = contents[0].split("\t")
            decoded = base64.b64decode(content_string[0])
            if row_count == "max":
                if read_cols == "all":
                    xanthos_data = pd.read_csv(io.StringIO(decoded.decode('cp1252')), error_bad_lines=False,
                                               warn_bad_lines=True)
                else:
                    xanthos_data = pd.read_csv(io.StringIO(decoded.decode('cp1252')), usecols=read_cols,
                                               error_bad_lines=False, warn_bad_lines=True)
            else:
                if read_cols == "all":
                    xanthos_data = pd.read_csv(io.StringIO(decoded.decode('cp1252')), nrows=row_count,
                                               error_bad_lines=False, warn_bad_lines=True)
                else:
                    xanthos_data = pd.read_csv(io.StringIO(decoded.decode('cp1252')), nrows=row_count,
                                               usecols=read_cols, error_bad_lines=False, warn_bad_lines=True)
    except Exception as e:
        print(e)
        return None
    return [xanthos_data, unit_display]


def process_input_years(contents, filename, filedate):
    file_data = process_file(contents, filename, filedate, years=0, row_count=0)[0]
    target_years = get_available_years(file_data)
    return target_years


def hydro_basin_lookup(basin_id, df_ref):
    # get which grid cells are associated with the target basin
    # target_idx_list = [k for k in df_ref.keys() if df_ref[:k] == basin_id]
    target_idx_list = df_ref[df_ref['basin_id'] == basin_id]
    return max(target_idx_list['grid_id'])
