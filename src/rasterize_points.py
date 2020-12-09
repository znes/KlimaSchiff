import os
import json

import geopandas as gpd
import pandas as pd
from shapely.geometry import box, mapping, Point
#from shapely import wkt

from geocube.api.core import make_geocube
#from geocube.rasterize import rasterize_points_griddata, rasterize_points_radial


with open("config.json") as file:
    config = json.load(file)

# data path with original intput data
datapath = os.path.join(
    os.path.expanduser("~"), config["intermediate_data"]
)

# path to store data
result_data = os.path.join(
    os.path.expanduser("~"), config["result_data"]
)

df = pd.read_csv(os.path.join(datapath, "ship_routes.csv"),
    index_col=0)

#df['geometry'] = df['geometry'].apply(wkt.loads)
df['geometry'] = df.apply(lambda x: Point((float(x.lon), float(x.lat))), axis=1)

geodf = gpd.GeoDataFrame(df, geometry='geometry')
geodf.crs= "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"

geo_grid = make_geocube(
    vector_data=geodf,
    measurements=['emission'],
    geom=json.dumps(mapping(box(-6, 48, 15, 70))),
    output_crs="+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs",
    resolution=(-0.1, 0.1),
    #rasterize_function=rasterize_points_griddata,
    fill=0
)
geo_grid.emission.plot()
