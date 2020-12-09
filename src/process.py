import os
import json
import numpy as np
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
datetimeformat = "%Y-%m-%d %H:%M:%S" # "%d/%m/%Y %H:%M:%S" #
datecol = "DATE TIME (UTC)" # "timestamp_pretty"

datapath = os.path.join(os.path.expanduser("~"), basepath, dataset)
result_path = os.path.join(os.path.expanduser("~"), basepath, "processed")

if not os.path.exists(result_path):
    os.makedirs(result_path)


files = os.listdir(datapath)
parser = lambda date: datetime.strptime(date, datetimeformat)

imo_numbers = []
chunks = []
for file in files:
    filecontent = open(os.path.join(datapath, file))

chunks = pd.read_csv(
        filecontent, sep=sep,
        #nrows=200000,
        parse_dates=[datecol],
        date_parser=parser, usecols=["DATE TIME (UTC)", "LONGITUDE", "LATITUDE", "IMO"]
    )
chunks.to_csv(os.path.join(result_path, "helcom_201501_processed_small.csv"))



#reader[reader["IMO"] == imo_numbers[0]].sort_values(by="DATE TIME (UTC)")
#
# s.set_index("imo", inplace=True)
# p = Polygon(points.values)
# hull = p.convex_hull
# a, b = hull.exterior.coords.xy
# collection = FeatureCollection(
#     [Feature(Point(lon, lat)) for lon, lat in tuple(list(zip(a, b)))]
# )
#
# with open(
#     os.path.join(result_path,
#     "{}_convex_hull.geojson".format(dataset)), "w"
# ) as outfile:
#     outfile.write(dumps(collection, indent=2))
#
# unique_df.drop_duplicates(subset=subset, inplace=True)
# unique_df.to_csv(os.path.join(result_path, "{}_unique_imo".format(dataset)))
