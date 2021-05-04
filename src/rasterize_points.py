import os
import json

import geopandas as gpd
import pandas as pd

from shapely.geometry import box, mapping

from functools import partial
from rasterio.enums import MergeAlg

from geocube.api.core import make_geocube
from geocube.rasterize import rasterize_image

from datacube.utils import geometry

from geojson import GeometryCollection

import matplotlib.pyplot as plt
from rasterio.features import rasterize

dataset = "vesselfinder"

with open("config.json") as file:
    config = json.load(file)

datapath = os.path.join(
    os.path.expanduser("~"),
    config["intermediate_data"],
    dataset,
    "ship_routes"
)

filepaths = [os.path.join(datapath, i) for i in os.listdir(datapath)]

# path to store data
result_data = os.path.join(
    os.path.expanduser("~"), config["result_data"]
)

df = pd.read_csv(filepaths[0], index_col=0, parse_dates=True) #, nrows=1000000)

geodf = gpd.GeoDataFrame(
    df, crs="epsg:4326",
    geometry=gpd.points_from_xy(df.lon, df.lat))

# reproject to geo dataframe right LCC
crs="+proj=lcc +lat_1=30 +lat_2=60 +lat_0=55 +lon_0=10 +y_0=1e+06 +x_0=1275000 +a=6370997 +b=6370997 +units=km +no_defs"
lcc_df = geodf.to_crs(crs)

# select data from one hour of year
lcc_hour = lcc_df.loc[(lcc_df.index.dayofyear == 1) & (lcc_df.index.hour == 0)]

# raster data -----------------------------------------------------------------
json_box = mapping(box(0, 0, 12*196, 12*196))
json_box["crs"] = {"properties": {"name": crs}}

geo_grid = make_geocube(
    vector_data=lcc_hour,
    measurements=['speed_calc', 'speed'],
    geom=json.dumps(json_box), # minx, miny, maxx, maxy
    #output_crs="+proj=lcc +lat_1=30 +lat_2=60 +lat_0=55 +lon_0=10 +y_0=1e+06 +x_0=1275000 +a=6370997 +b=6370997 +units=km +no_defs",
    resolution=(-12, 12),
    rasterize_function=partial(rasterize_image, merge_alg=MergeAlg.add),
    fill=0,
    #align=(0, 0)
)
geo_grid["speed"].plot()
geo_grid


# raster alternative ---------------------------------------------------------
# but this is just what geocube does under the hood...
crs="+proj=lcc +lat_1=30 +lat_2=60 +lat_0=55 +lon_0=10 +y_0=1e+06 +x_0=1275000 +a=6370997 +b=6370997 +units=km +no_defs"
geopoly = geometry.Geometry(
    mapping(box(0, 0, 12*196, 12*196)),
    crs=crs
)
geobox = geometry.GeoBox.from_geopolygon(
            geopoly, (-12, 12), crs=crs
        )
# test as geojson in lon/lat
json_poly = GeometryCollection([geopoly.to_crs(crs="EPSG:4326").json])

#aff = transform.from_bounds(-1275, -1000, -1275+12*195, -1000+12*195, 195, 195)
arr = rasterize(
    zip(lcc_df.iloc[1:100000].geometry.apply(mapping).values, lcc_df.iloc[1:100000].speed_calc),
    out_shape=(geobox.height, geobox.width),
    transform=geobox.affine,
    merge_alg=MergeAlg.add,
    all_touched=True
)

fig, ax = plt.subplots()
im = ax.imshow(pd.DataFrame(arr).clip(upper=3000).values)
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel("Emission", rotation=-90, va="bottom")


#-----------------------------------------
# check with EPSG:
# geopoly = geometry.Geometry(
#     mapping(box(-6, 48, 15, 70)),
#     crs="EPSG:4326"
# )
# json_poly = GeometryCollection([geopoly.json])
#
# aff = transform.from_bounds(-6, 48, 15, 70, 196, 196)
# arr = rasterize(
#     zip(geodf.iloc[0:100000].geometry.apply(mapping).values, geodf.iloc[0:100000].speed_calc),
#     out_shape=(196, 196),
#     transform=aff,
#     merge_alg=MergeAlg.add,
#     all_touched=True
# )
# fig, ax = plt.subplots()
# im = ax.imshow(pd.DataFrame(arr).clip(upper=300).values
# )
# cbar = ax.figure.colorbar(im, ax=ax)
# cbar.ax.set_ylabel("Emission", rotation=-90, va="bottom")

#lcc.iloc[0:100000].to_file("data/test.shp", driver="ESRI Shapefile")
