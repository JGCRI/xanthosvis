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
Set up Xanthos using the following steps:
1.  This repository uses the Git Large File Storage (LFS) extension (see https://git-lfs.github.com/ for details).  Please install GitLFS and run the following command before cloning if you do not already have Git LFS initialized:
`git lfs install`.
2.  Clone Xanthos into your desired location `git clone https://github.com/JGCRI/xanthos.git`.  Some Windows users have had better luck with `git lfs clone https://github.com/JGCRI/xanthos.git`
3.  Make sure that `setuptools` is installed for your Python version.  This is what will be used to support the installation of the Xanthos package.
4.  From the directory you cloned Xanthos into run `python setup.py install` .  This will install Xanthos as a Python package on your machine and install of the needed dependencies.  If installing in an HPC environment, a community user advised that it is best to install the anaconda environment before running the installation command.  HPC environments may also require the use of the `--user` flag in the install command to avoid permissions errors.
5.  Setup your configuration file (.ini).  Examples are located in the "example" directory.  Be sure to change the root directory to the directory that holds your data (use the `xanthos/example` directory as an example).
6. If running Xanthos from an IDE:  Be sure to include the path to your config file.  See the "xanthos/example/example.py" script as a reference.
7. If running Xanthos from terminal:  Run model.py found in xanthos/xanthos/model.py passing the full path to the config file as the only argument. (e.g., `python model.py <dirpath>/config.ini`).

# Links
Xanthos DOI
[![DOI](https://zenodo.org/badge/88797535.svg)](https://zenodo.org/badge/latestdoi/88797535) [![Build Status](https://travis-ci.org/JGCRI/xanthos.svg?branch=master)](https://travis-ci.org/JGCRI/xanthos)

