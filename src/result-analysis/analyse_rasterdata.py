# import folium
# from folium import plugins
import geopandas as gpd
import pandas as pd
import os

# import contextily as cx
import matplotlib.pyplot as plt
import xarray as xr
import json
import matplotlib as mpl

with open("config.json") as file:
    config = json.load(file)


nc_dirpath = os.path.join(
    os.path.expanduser("~"), config["result_data"], "2015_sq"
)
ds = []
for file in os.listdir(nc_dirpath):
    if file.endswith("NOx.nc"):
        nc_filepath = os.path.join(nc_dirpath, file)
        ds.append(
            xr.open_dataset(nc_filepath).rename({"sum": file.strip(".nc")})
        )
da = xr.merge(ds)

res = {}
for poll in ds:
    for poll2 in poll:
        for t in poll[poll2]:
            res[poll2, t.time.values] = float(t.sum().values)

pd.Series(res).unstack().T.loc["2015"].to_csv(
    "rastered_emissions_2015_as_tseries.csv"
)

#
#
# select.plot(
#     cmap=mpl.cm.RdYlBu_r,
#     norm=mpl.colors.LogNorm(
#         vmin=float(select.min()) + 100, vmax=float(select.max())
#         ),)
