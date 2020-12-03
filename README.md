[![Build Status](https://travis-ci.org/crvernon/xanthosvis.svg?branch=master)](https://travis-ci.org/crvernon/xanthosvis)
[![codecov](https://codecov.io/gh/crvernon/xanthosvis/branch/master/graph/badge.svg)](https://codecov.io/gh/crvernon/xanthosvis)

# GCIMS Hydrologic Explorer
The Global Change Intersectoral Modeling System (GCIMS) Hydrologic Explorer (HE) interactive dashboard, written in Python, is designed for visualizing GCIMS hydrolgoic data outputs from hydrology components in a time-series, aggregated format. 
Currently, the system is capable of viewing outputs from data containing total runoff, average streamflow, potential evapotranspiration, and actual evapotranspiration. The system has been designed
to handle other types of future hydrologic outputs as well for further expansion. The system is currently able to accept data outputs in csv (or zipped csv for quicker uploads) format 
from Xanthos, an open-source hydrologic model designed to quantify and analyze global water availability. The system is capable of viewing the aggregated outputs by country, water basin 
(basins are from the  Global Change Assessment Model (GCAM)), and 0.5 degree geographic grid cells.

# Contact Us
For questions, technical supporting and user contribution, please contact:

Evanoff, Jason <Jason.Evanoff@pnnl.gov>

Vernon, Chris <Chris.Vernon@pnnl.gov>

# Notice
The GCIMS HE currently only supports Python 3.7+, Dash 1.5+, and Plotly 4.0+. Please note the requirements.txt file for more detailed requirements.

# Get Started 
There are two ways to access the GCIMS Hydrologic Explorer. The first method is to access the public website at -----------. The second method is to install
the package locally using the following steps:
1.  Clone the GCIMS HE to your preferred location using 'git clone https:/'github.com/JGCRI/-------'
2.  Make sure that `setuptools` is installed for your Python version.  This is what will be used to support the installation.
3.  From the directory you cloned GCIMS HE into run `python setup.py install` .  This will install GCIMS HE as a Python package on your machine and install of the needed dependencies.  If installing in an HPC environment, a community user advised that it is best to install the anaconda environment before running the installation command.  HPC environments may also require the use of the `--user` flag in the install command to avoid permissions errors.

# Links
Xanthos DOI
[![DOI](https://zenodo.org/badge/88797535.svg)](https://zenodo.org/badge/latestdoi/88797535) [![Build Status](https://travis-ci.org/JGCRI/xanthos.svg?branch=master)](https://travis-ci.org/JGCRI/xanthos)

