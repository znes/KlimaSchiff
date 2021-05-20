import os
import json

import geopandas as gpd
import pandas as pd
import numpy as np
import xarray as xr

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


with open("config.json") as file:
    config = json.load(file)

datapath = os.path.join(
    os.path.expanduser("~"), config["intermediate_data"], "ship_emissions",
)

filepaths = [os.path.join(datapath, i,) for i in os.listdir(datapath)]

# path to store data
result_data = os.path.join(os.path.expanduser("~"), config["result_data"])


# reproject to geo dataframe right LCC
crs = "epsg:4326"  # LCC "+proj=lcc +lat_1=30 +lat_2=60 +lat_0=55 +lon_0=10 +y_0=1e+06 +x_0=1275000 +a=6370997 +b=6370997 +units=km +no_defs"

resolution = (
    -0.05,
    0.065,
)  # (-12, 12) for LCC

json_box = mapping(
    box(-4, 48, 30, 68,)
)  #  0, 0, 12 * 196, 12 * 196 for LCC minx miny maxx maxy
json_box["crs"] = {"properties": {"name": crs}}

geopoly = geometry.Geometry(json_box, crs=crs,)
geobox = geometry.GeoBox.from_geopolygon(geopoly, resolution, crs=crs,)

coords = affine_to_coords(geobox.affine, geobox.width, geobox.height)

emission_types = [
    "SOx (Well to tank) [kg]",
    "CO2 (Well to tank) [kg]",
]

emissions_per_day = {}
dates = []
for emission_type in emission_types:
    for file in filepaths[0:2]:
        df = pd.read_csv(
            file, index_col=[0], parse_dates=True
        )  # , nrows=1000000)

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
                geodf[geodf[emission_type]].clip(lower=0),
            ),  # colums 7 is co2
            out_shape=(geobox.height, geobox.width,),
            transform=geobox.affine,
            merge_alg=MergeAlg.add,
            all_touched=True,
        )
        date = df.index.date[0].strftime("%Y-%m-%d")
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

    da.to_netcdf(os.path.join(result_data, emission_type + ".nc"))


# import matplotlib.pyplot as plt
# fig, ax = plt.subplots()
# im = ax.imshow(pd.DataFrame(arr).clip(upper=300).values)
# cbar = ax.figure.colorbar(im, ax=ax)
# cbar.ax.set_ylabel("Emission", rotation=-90, va="bottom")


f = xr.open_dataset("data/CAMS-Globship_comb_himoses__2015__CO2.nc")
