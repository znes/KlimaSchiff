"""
Get set of unique imo numbers from ship routes
"""
import os
import json

import pandas as pd

with open("config.json") as file:
    config = json.load(file)

dirpath = os.path.join(
    os.path.expanduser("~"),
    config["intermediate_data"],
    "ship_routes")

files = os.listdir(
        dirpath
    )

imos = []
for file in files:
    print(file)
    imos.extend(pd.read_csv(os.path.join(dirpath, file), usecols=["imo"], dtype="int").imo.unique())

outpath = os.path.join(
    os.path.expanduser("~"),
    config["model_data"])

if not os.path.exists(outpath):
    os.path.makedirs(outpath)

unique_imos = set(imos)
pd.Series(list(unique_imos)).to_csv(
    os.path.join(
        os.path.expanduser("~"),
        config["model_data"],
        "unique_imos.csv"))
