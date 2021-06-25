import os
import json

import geopandas as gpd
import pandas as pd
import numpy as np
import xarray as xr
import logging
import matplotlib.pyplot as plt


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
# from logger import logger


def get_lcc_bounds(bounding_box, to_shp=False):
    """
    """
    lon, lat = bounding_box.exterior.coords.xy
    geodf = gpd.GeoDataFrame(
        crs="epsg:4326", geometry=gpd.points_from_xy(lon, lat),
    )
    geodf.drop(4, inplace=True)
    geodf.index = ["lower right", "upper right", "upper left", "lower left"]

    geodf = geodf.to_crs(
        "+proj=lcc +lat_1=30 +lat_2=60 +lat_0=55 +lon_0=10 +y_0=0 +x_0=0 +a=6370997 +b=6370997 +units=m +no_defs"
    )
    if to_shp:
        geodf.to_file(driver="ESRI Shapefile", filename="area.shp")
    return geodf


def plot_array(array, lower=0, upper=3000):
    """
    """
    fig, ax = plt.subplots()
    im = ax.imshow(pd.DataFrame(array).clip(lower=lower, upper=upper).values)
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Emission", rotation=-90, va="bottom")


def rasterize_points(
    config=None,
    emission_types={
        "SOx [kg]": "SO2",
        "PM [kg]": "PM",
        "NOx [kg]": "NOx",
        "CO2 [kg]": "CO2",
        "BC [kg]": "BC",
        "ASH [kg]": "ASH",
        "POA [kg]": "POA",
        "CO [kg]": "CO",
        "NMVOC [kg]": "NMVOC",
    }
    # resolution=(-0.03, 0.05),
    # bbox=[-4, 50, 25, 65],
):
    """
    """
    if config is None:
        logging.info("No config file provided, trying to read...")
        with open("config.json") as file:
            config = json.load(file)

    resolution = config["resolution"]
    bbox = config["bounding_box"]

    datapath = os.path.join(
        os.path.expanduser("~"), config["intermediate_data"], "ship_emissions",
    )

    filepaths = [os.path.join(datapath, i,) for i in os.listdir(datapath)]
    filepaths.sort()

    # path to store data
    result_data = os.path.join(os.path.expanduser("~"), config["result_data"])

    if not os.path.exists(result_data):
        os.makedirs(result_data)

    # reproject to geo dataframe right LCC
    crs = "epsg:4326"  # LCC "+proj=lcc +lat_1=30 +lat_2=60 +lat_0=55 +lon_0=10 +y_0=1e+06 +x_0=1275000 +a=6370997 +b=6370997 +units=km +no_defs"

    bounding_box = box(bbox[0], bbox[1], bbox[2], bbox[3])

    json_box = mapping(bounding_box)  # minx miny maxx maxy

    json_box["crs"] = {"properties": {"name": crs}}

    geopoly = geometry.Geometry(json_box, crs=crs,)
    geobox = geometry.GeoBox.from_geopolygon(
        geopoly, resolution, crs=crs,
    )  # resolution y,x

    # geobox.xr_coords() # also get coords as xarrays from geobox
    coords = affine_to_coords(geobox.affine, geobox.width, geobox.height)

    for emission_type in emission_types.keys():
        logging.info("Rasterizing emissions for type: {}.".format(emission_type))
        emissions_per_day = {}
        dates = []
        for file in filepaths:
            df = pd.read_csv(
                file, index_col=[0], parse_dates=True
            )  # , nrows=1000000)

            # add both engine types
            df[emission_type] = (
                df["Propulsion-" + emission_type]
                + df["Electrical-" + emission_type]
            )

            geodf = gpd.GeoDataFrame(
                df,
                crs="epsg:4326",
                geometry=gpd.points_from_xy(df.lon, df.lat),
            )

            if "lcc" in crs:
                geodf = geodf.to_crs(crs)
            arr = rasterize(
                zip(
                    geodf.geometry.apply(mapping).values, geodf[emission_type],
                ),  # colums 7 is co2
                out_shape=(geobox.height, geobox.width,),
                transform=geobox.affine,
                merge_alg=MergeAlg.add,
                all_touched=True,
            )

            date = df.index[
                0
            ].dayofyear  # df.index.date[0].strftime("%Y-%m-%d")
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
                result_data, emission_types[emission_type] + ".nc"
            ),  # write to shorter file name
            encoding={
                "lat": {"dtype": "float32"},
                "lon": {"dtype": "float32"},
                "sum": {"dtype": "float32"},
            },
        )
#rasterize_points()
