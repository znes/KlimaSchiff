import os
import json

import geopandas as gpd
import pandas as pd

from shapely.geometry import box, mapping

#from functools import partial
from rasterio.enums import MergeAlg

#from geocube.api.core import make_geocube
#from geocube.rasterize import rasterize_image

from datacube.utils import geometry

from geojson import GeometryCollection
import xarray as xr

import matplotlib.pyplot as plt
from rasterio.features import rasterize

dataset = "vesselfinder"

with open("config.json") as file:
    config = json.load(file)

datapath = os.path.join(
    os.path.expanduser("~"),
    config["intermediate_data"],
    dataset,
    "ship_routes",
)

filepaths = [os.path.join(datapath, i) for i in os.listdir(datapath)]

# path to store data
result_data = os.path.join(os.path.expanduser("~"), config["result_data"])

df = pd.read_csv(
    filepaths[0], index_col=0, parse_dates=True
)  # , nrows=1000000)

geodf = gpd.GeoDataFrame(
    df, crs="epsg:4326", geometry=gpd.points_from_xy(df.lon, df.lat)
)

# reproject to geo dataframe right LCC
crs = "epsg:4326" # LCC "+proj=lcc +lat_1=30 +lat_2=60 +lat_0=55 +lon_0=10 +y_0=1e+06 +x_0=1275000 +a=6370997 +b=6370997 +units=km +no_defs"
resolution = (0.05, 0.065) # (-12, 12) for LCC
json_box = mapping(box(-6, 48, 15, 70)) #  0, 0, 12 * 196, 12 * 196 for LCC
json_box["crs"] = {"properties": {"name": crs}}

if "lcc" in crs:
    geodf = geodf.to_crs(crs)


geopoly = geometry.Geometry(json_box, crs=crs)
geobox = geometry.GeoBox.from_geopolygon(geopoly, resolution, crs=crs)

emissions = {}
year = []
daysofyear = geodf.index.dayofyear.unique()[0:3]
for day in daysofyear:

    emis_day = geodf.loc[(geodf.index.dayofyear == day)]

    arr = rasterize(
        zip(
            emis_day.geometry.apply(mapping).values,
            emis_day.speed_calc,
        ),
        out_shape=(geobox.height, geobox.width),
        transform=geobox.affine,
        merge_alg=MergeAlg.add,
        all_touched=True,
    )
    year.append(arr)

da = xr.DataArray(
    year,
    dims=["day", "lat", "lon"],
    coords=[daysofyear,range(1, geobox.height+1),range(1, geobox.width+1)] )
da.attrs = {"var_dsec": "Model species CO2", "long_name": "CO2", "units": "kg/day"}
da.to_netcdf("emissions.nc")

#emissions[str(day)] = da
#ds = ds.assign_coords({"TSTEP": 1, "LAY": 1})
#ds = ds.expand_dims({"TSTEP": 1, "LAY": 1})
#ds = xr.Dataset(emissions)

# fig, ax = plt.subplots()
# im = ax.imshow(pd.DataFrame(arr).clip(upper=300).values)
# cbar = ax.figure.colorbar(im, ax=ax)
#cbar.ax.set_ylabel("Emission", rotation=-90, va="bottom")


#
# import gdal
# import osr
#
# srs = osr.SpatialReference()
# srs.ImportFromEPSG(4326)
# dst_filename = 'day1.tiff'
# x_pixels = geobox.width  # number of pixels in y
# y_pixels = geobox.height  # number of pixels in x
# driver = gdal.GetDriverByName('GTiff')
# dataset = driver.Create(dst_filename, x_pixels, y_pixels, 1, gdal.GDT_Float32)
# dataset.GetRasterBand(1).WriteArray(arr)
# dataset.SetGeoTransform(geobox.affine.to_gdal())
# dataset.SetProjection(srs.ExportToWkt())
# dataset.FlushCache()
# dataset=None

#
f = xr.open_dataset("data/case2016_A_PublicPower2016")
f["CO"]
