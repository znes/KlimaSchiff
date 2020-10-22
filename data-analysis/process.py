import os
import json

import pandas as pd
from datetime import datetime

from shapely.geometry import Point, Polygon, LineString
from shapely_geojson import dumps, Feature, FeatureCollection

#
# create unique imo data set for helcom data on local machine with data on
# server
#
basepath = "klimaschiff/data"
subset = "IMO"  # IMO
sep = "," # ;
dataset = "vesselfinder" # vesselfinder
datetimeformat = "%Y-%d-%m %H:%M:%S" # "%d/%m/%Y %H:%M:%S" #
datecol = "DATE TIME (UTC)" # "timestamp_pretty"

datapath = os.path.join(os.path.expanduser("~"), basepath, dataset)
result_path = os.path.join(os.path.expanduser("~"), basepath, "processed")

if not os.path.exists(result_path):
    os.makedirs(result_path)


files = os.listdir(datapath)
parser = lambda date: datetime.strptime(date, datetimeformat)

unique_df = pd.DataFrame()
points = pd.DataFrame()
for file in files:
    filecontent = open(os.path.join(datapath, file))
    reader = pd.read_csv(
        filecontent, sep=sep, nrows=200000, parse_dates=[datecol],
        date_parser=parser
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
