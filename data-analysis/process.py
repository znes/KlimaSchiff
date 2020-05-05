import os
import json

import pandas as pd

from shapely.geometry import Point, Polygon, LineString
from shapely_geojson import dumps, Feature, FeatureCollection

#
# create unique imo data set for helcom data on local machine with data on
# server
#
basepath = "/home/admin/klimaschiff/data"
subset = "imo"  #
dataset = "helcom"
result_path = os.path.join(basepath, "processed")
datapath = os.path.join(basepath, dataset)

if not os.path.exists(result_path):
    os.makedirs(result_path)

files = os.listdir(datapath)

unique_df = pd.DataFrame()

points = pd.DataFrame()
for file in files:
    filecontent = open(os.path.join(datapath, file))
    reader = pd.read_csv(
        filecontent, sep=";", chunksize=200000
    )
    for chunk in reader:
        unique_df = pd.concat(
            [unique_df, chunk.drop_duplicates(subset=subset)]
        )
        points = pd.concat([points, chunk[["imo", "long", "lat"]]])

points.set_index("imo", inplace=True)
p = Polygon(points.values)
hull = p.convex_hull
a, b = hull.exterior.coords.xy
collection = FeatureCollection(
    [Feature(Point(lon, lat)) for lon, lat in tuple(list(zip(a, b)))]
)

with open(
    os.path.join(result_path,
    "{}_convex_hull.geojson".format(dataset)), "w"
) as outfile:
    outfile.write(dumps(collection, indent=2))

unique_df.drop_duplicates(subset=subset, inplace=True)
unique_df.to_csv(os.path.join(result_path, "{}_unique_imo".format(dataset)))
