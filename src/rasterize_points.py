import os
import json

import geopandas as gpd
import pandas as pd
import numpy as np
import xarray as xr
import logging

from shapely.geometry import (
    box,
    mapping,
)

from rasterio.enums import MergeAlg
from rioxarray.rioxarray import affine_to_coords
from rasterio.features import rasterize

from datacube.utils import geometry

# from geocube.api.core import make_geocube
# from geocube.rasterize import rasterize_image
# from functools import partial

#from logger import logger

with open("config.json") as file:
    config = json.load(file)

datapath = os.path.join(
    os.path.expanduser("~"), config["intermediate_data"], "ship_emissions",
)

filepaths = [os.path.join(datapath, i,) for i in os.listdir(datapath)]

# path to store data
result_data = os.path.join(os.path.expanduser("~"), config["result_data"])
if not os.path.exists(result_data):
    os.makedirs(result_data)

# reproject to geo dataframe right LCC
crs = "epsg:4326"  # LCC "+proj=lcc +lat_1=30 +lat_2=60 +lat_0=55 +lon_0=10 +y_0=1e+06 +x_0=1275000 +a=6370997 +b=6370997 +units=km +no_defs"

latDistance = 4 # km
longDistance = 4 # km
latdegree = latDistance / 110.574
londegree= longDistance / (111.320 * np.cos(latdegree / np.pi / 180))


resolution = (
    -0.03617,
     0.03593,
)  # (-12, 12) for LCC

bounding_box = box(-4, 50, 25, 65,)
json_box = mapping(
    bounding_box
)  #  0, 0, 12 * 196, 12 * 196 for LCC minx miny maxx maxy
json_box["crs"] = {"properties": {"name": crs}}


# for lcc reference points
# lon, lat = bounding_box.exterior.coords.xy
# _geodf = gpd.GeoDataFrame(crs="epsg:4326", geometry=gpd.points_from_xy(lon, lat),
#     )
# _geodf = _geodf.to_crs("+proj=lcc +lat_1=30 +lat_2=60 +lat_0=55 +lon_0=10 +y_0=1e+06 +x_0=1275000 +a=6370997 +b=6370997 +units=km +no_defs")
# _geodf.to_json()

geopoly = geometry.Geometry(json_box, crs=crs,)
geobox = geometry.GeoBox.from_geopolygon(geopoly, resolution, crs=crs,) # resolution y,x

# geobox.coords["latitude"]
#geobox.xr_coords() # also get coords as xarrays from geobox
coords = affine_to_coords(geobox.affine, geobox.width, geobox.height)


emission_types = {
    "NOx [kg]": "NOx",
    "CO2 [kg]": "CO2"
}

for emission_type in emission_types.keys():
    emissions_per_day = {}
    dates = []
    for file in filepaths:
        df = pd.read_csv(
            file, index_col=[0], parse_dates=True
        )  # , nrows=1000000)
        counting = df[df["speed_calc"] > 15].count()["imo"]
        logging.info("Dropping {} points > 13 m/s in {}".format(counting, file))
        df = df[df["speed_calc"] < 15] # only use data with speed lower 13 m/s

        geodf = gpd.GeoDataFrame(
            df, crs="epsg:4326", geometry=gpd.points_from_xy(df.lon, df.lat),
        )

        if "lcc" in crs:
            geodf = geodf.to_crs(crs)

            # geodf.to_file("test.shp", driver="ESRI Shapefile")
        emissions = {}
        year = []

        arr = rasterize(
            zip(
                geodf.geometry.apply(mapping).values,
                geodf[emission_type],
            ),  # colums 7 is co2
            out_shape=(geobox.height, geobox.width,),
            transform=geobox.affine,
            merge_alg=MergeAlg.add,
            all_touched=True,
        )

        date = df.index[0].dayofyear #df.index.date[0].strftime("%Y-%m-%d")
        dates.append(date)
        emissions_per_day[date] = arr

    da = xr.DataArray(
        [i for i in emissions_per_day.values()],
        dims=["time", "lat", "lon",],
        coords=[np.array(dates), coords["y"], coords["x"],],
    )

    da = da.rename("sum")
    da = da.astype("float64")
    da.attrs = {"units": "kg d-1"}

    da.coords["time"].attrs = {
        "standard_name": "time",
        "calendar": "proleptic_gregorian",
        "units": "days since 2015-01-01",
        "axis": "T",
    }
    da.coords["lon"].attrs = {
        "standard_name": "longnitude",
        "long_name": "longnitude",
        "units": "degrees_east",
        "axis": "X",
    }
    da.coords["lat"].attrs = {
        "standard_name": "latitude",
        "long_name": "latitude",
        "units": "degrees_north",
        "axis": "Y",
    }

    da.to_netcdf(
        os.path.join(
            result_data,
            emission_types[emission_type] + ".nc"), # write to shorter file name
        encoding={
            "lat": {"dtype": "float32"},
            "lon": {"dtype": "float32"},
            "sum": {"dtype": "float32"},
        },
    )

import matplotlib.pyplot as plt
fig, ax = plt.subplots()
im = ax.imshow(pd.DataFrame(arr).clip(lower=0).values)
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel("Emission", rotation=-90, va="bottom")


f = xr.open_dataset("data/CAMS-Globship_comb_himoses__2015__CO2.nc")

# day1 = f["sum"][0]

# def to_tif(filename, array):
#     """
#     """
#     import gdal
#
#     dst_filename = "A" + '.tiff'
#     x_pixels = len(da.coords["lon"])  # number of pixels in x
#     y_pixels = len(da.coords["lat"])  # number of pixels in y
#     driver = gdal.GetDriverByName('GTiff')
#     dataset = driver.Create(dst_filename,x_pixels, y_pixels, 1,gdal.GDT_Float32)
#     dataset.GetRasterBand(1).WriteArray(da[0].values)
#
#     # follow code is adding GeoTranform and Projection
#     geotrans=dataset.GetGeoTransform()  #get GeoTranform from existed 'data0'
#     #proj=dataset.GetProjection() #you can get from a exsited tif or import
#     dataset.SetGeoTransform(geotrans)
#     dataset.SetProjection("epsg:4326")
#     dataset.FlushCache()
#     dataset=None
