# GCIMS Hydrologic Explorer Guide & Tutorial
The Global Change Intersectoral Modeling System (GCIMS) Hydrologic Explorer (HE) is an interactive dashboard, written in 
Python, designed to visualize GCIMS hydrologic data outputs from hydrology components in a time-series, aggregated
format. Currently, the system is capable of viewing outputs from data containing total runoff, average streamflow, 
potential evapotranspiration, and actual evapotranspiration and has been designed to handle other types of 
future hydrologic outputs as well for further expansion. The system is currently able to accept data input files in 
csv (or zipped csv for quicker uploads) format from Xanthos, an open-source hydrologic model designed to quantify and 
analyze global water availability. The system is capable of viewing the aggregated outputs by country, water basin 
(basins are from the  Global Change Assessment Model (GCAM)), and 0.5 degree geographic grid cells.

This guide and tutorial will outline the key components of the application and provide a sample scenario designed to 
give you an idea of how to 

To run this vignette, you will need to access the GCMIS HE online application at ---------- 
or install and setup the package locally.

## Setup
All that is needed is to access the online web application for GCIMS HE at ------. If installing the package locally 
--- (need info here)

## Interface Guide

### Loading Data
Once you have the web page loaded, or set up the package locally, you will see the application home page, which contains 
the input controls on the left, and the instructions/output tabs on the right. To get started using the dashboard, 
a data input file must first be uploaded to the system via the 'Data Upload' component. This component works similar to 
other file upload components and also supports drag and drop. Currently, the system only supports data files from
Xanthos but there plans to include other systems in the future.

### Setting Options 
Once you have loaded a data file, the next step is to set the options and parameters that control and filter the output. 
Below the file upload control are several controls:
- The statistic option controls how the data is aggregated
- The units option allows you to switch between available unit choices
- The start and end date control the range of data included in the output
- The view by option controls whether the data is aggregated by country or GCAM water basin
- The filter by months option allows you to select individual months to filter by. For example
if you just wanted to view runoff in January and February, the system will limit the output to just 
those months but for all the years in the range.
- The view as gridded data option changes the aggregation area to each individual grid cell. Instead 
of seeing the map by country or basin, you will see each grid cell color coded individually.

### Interfacing with the Map
Once you have loaded data and selected your options, a choropleth map (or scatter map if you
selected the gridded view) will load in the main output area. There are a number of map controls located in the 
upper right hand corner of the map that control basic functions like zoom and pan. Clicking on an area on the map will
load a line graph below the main map with detailed time-series information on the area you clicked on. You can also 
select a subset of areas by using the box select or lasso tool. This will limit the map to those areas and rescale
the data based on the limited subset. 

### Using the Detailed Area Information Graph
The detailed area information graph is available by clicking on a region or grid cell in the main map. The system will 
load the corresponding data for that region in the line graph below the main map. This graph shows the full time-series
data for that region for the months/years selected only.

### Output
The primary form of output is to save a high resolution image of the current map/graph by clicking on the download plot
button available in the upper right hand of the map/graph. This will automatically save a high resolution image of your
current view that is suitable for presentation/papers.

## Tutorial - Using the Full Capabilities of the System
The goal of this tutorial is to show all of the steps needed to view runoff for the east coast of the United States 
during the spring. This tutorial covers all of the steps needed to load, view, filter, and save output from Xanthos 
in the GCIMS HE. It will also cover how to interact with the map and graph controls and select subsets of regions.

Tutorial Step 1: Load Data | Example
--------------- | -------
To begin the tutorial, load the sample data file from the package using the 'Upload Data' control. This file contains 
xxxxx. This will load the data file into the system for processing. | ![Run Scenario](vig1.png){width=100% height=20%} 

Tutorial Step 2: Set Options | Example
--------------- | -------
After loading data, the system will populate the dropdowns with available options. The statistic choices are always 
the same however, and for now just leave it at 'mean'. The start and end dates will be populated with the max and min 
values from the data, and leave those as the defaults for now. For the view by option, leave it as basin, and then click
'load data'.

Tutorial Step 3: Map Select | Example
--------------- | -------
After clicking load data, you should see a choropleth map of the world separated by country. There are a number of 
options we can change to get to our desired goal, but let's start first with focusing on the United States. Select the 
box select tool in the upper right hand corner and drag it over just the United States. It should highlight the
basins as you expand the selection over them. This will zoom the map to your selection area and rescale the legend to
match the selected region's data values. You should see now a selection of basins that cover the majority of the United
States. 

Tutorial Step 4: Using the Lasso | Example
--------------- | -------
Now that we have the United States as the focus, we want to further refine that to just the east coast. Click on the 
lasso select tool in the upper right hand corner and starting from below Florida, select to the north and then 
northeast along approximately the eastern side of the appalachian mountains up through Maine. Your map should now contain 
the south atlantic, mid atlantic and new england basins. (It's ok if there are other basins selected for now, however
you can always restart the process by clicking the 'Reset Graph' button and following these steps again.)

Tutorial Step 5: Using the Grid View | Example
--------------- | -------
In order to further refine that granularity of the data to the coastal regions, we will need to separate the data into
grid cells. Do this by selecting the toggle switch 'View as Gridded Data' and then click the 'Load Data' button again.
You should now see a collection of colored grid cells in place of the basins. It is important to note here that while
in the grid view mode, the box select tool 'snaps' to the region (country or basin) and will include the entire region 
if you select any of it's cells, while the lasso tool will NOT snap and will allow you to select individual cells.

Tutorial Step 6: Filtering by Month| Example
--------------- | -------
Now that we have the grid cells separated, we want to know the values for just spring, so we will need to filter by month.
In the options panel, click the 'Filter by Months' dropdown and choose March - June for months that contain spring. Since
spring is usually associated with the most rainfall, you should see expanded numbers on the legend as well as some 
different grid cell values with the change in months. Feel free to toggle between the gridded and non-gridded views to
view the data by basin as well.

Tutorial Step 7: Using the Area Detail Graph | Example
--------------- | -------
Whether viewing by grid cell of basin, to see the full time series for a region, just single click on that region on 
the map and the time series will load in the graph below. Note how the graph most likely looks pretty jagged, this is 
because we filtered the months to just the spring months. The area detail graph will reflect all of your chosen options.

Tutorial Step 8: Output & Conclusion | Example
--------------- | -------
To create output, use the snapshot tool located in the upper right toolbar of the map or graph to save your current 
view to a high resolution image. Feel free to adjust the options such as modifying the statistic to max or min, 
choosing a different range of months, or reset the graph and view a different region of the world. 

## Conclusion
This concludes the tutorial. At this point you should be familiar with all of the major concepts and actions available 
within the system and how to filter data and regions. 