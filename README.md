# KlimaSchiff


## Install on Linux

Setup a virtualenv, activate and install dependencies via pip:

```
  virtualenv -p python3.6 venv
  virtualenv venv/bin/activate
  pip install -r requirements.txt
```

You might need to install GDAL and its necessary dependencies first using
the following commands (linux):

```
sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable && sudo apt-get update
sudo apt-get install gdal-bin
sudo apt-get install libgdal-dev python3.6-dev g++
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
pip install GDAL==3.0.4  # optionally as it is also within the requirements.txt
```

For GDAL 3.0.4 the unstable repository is required. Make sure that you gdal version
matches the one you use with the pip command. To find out your gdal version you do:

`gdal-config --version`

## Usage

The software allows to do the following things:

* merge helcom and vesselfinder data set
* generate ships routes (5min intervall by default)
* calculate emissions for the ships routes
* rasterize the emissions and write to netcdf

Everyone of the steps depends on the step before it. Therefore, to use the code,
you will need the raw data sets used.  

sudo usermod -aG sudo klimaschiff
