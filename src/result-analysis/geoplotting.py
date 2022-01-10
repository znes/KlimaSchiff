# import folium
# from folium import plugins
import geopandas as gpd
import pandas as pd
import os
#import contextily as cx
import matplotlib.pyplot as plt
import xarray as xr
import json
import matplotlib as mpl
from matplotlib.patches import Rectangle
with open("config.json") as file:
    config = json.load(file)


nc_dirpath = os.path.join(
    os.path.expanduser("~"),
    config["result_data"],
    "2015_sq"
)
ds = []
for file in os.listdir(nc_dirpath):
    nc_filepath = os.path.join(
        nc_dirpath, file
    )
    ds.append(xr.open_dataset(nc_filepath).rename({"sum": file.strip(".nc")}))

pollutants = xr.merge(ds)
#select = ds.sum("time")["sum"]
#ds["sum"].isel(time=1)
pollutant = "CO2"
select = pollutants.sum("time")[pollutant]
#select = select / 1e6 # kg -> Gg
fig, ax = plt.subplots()
select.plot(
    ax=ax,
    cmap=mpl.cm.RdYlBu_r,
    norm=mpl.colors.LogNorm(
        vmin=float(select.min())+100,
        vmax=float(select.max())),
        cbar_kwargs={
        #"orientation": "horizontal",
        "label": "CO2 emissions in kg",
        #"pad": 0.1,
    }
)
ax.add_patch(Rectangle((-5, 48), 20, 20, fill=False, color="red"))
plt.text(-3.5, 64, 'Vesselfinder', color="red")
plt.text(20, 52, 'Helcom', color="red")
plt.savefig("figures/{}-emissions.pdf".format(pollutant))



# data_path = os.path.join(
#     os.path.expanduser("~"),
#     config["intermediate_data"],
#     #"2015_sq",
#     "ship_routes"
# )
#
# file = os.path.join(
#     data_path,
#     os.listdir(data_path)[1])
#
# df = pd.read_csv(file)
# df.lon.max()
# geometry = gpd.points_from_xy(df.lon, df.lat)
# gdf = gpd.GeoDataFrame(df, geometry=geometry)

#
# m=folium.Map([54,10],zoom_start=5)
# heat_data = [[point.xy[1][0], point.xy[0][0]] for point in gdf.geometry ]
# plugins.HeatMap(heat_data, radius=2, blur=2).add_to(m)
# m.save('heatmap.html')
