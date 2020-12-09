import os
import json

import pandas as pd
from datetime import datetime

import dask.dataframe as dd

dataset = "vesselfinder"

with open("config.json") as file:
    config = json.load(file)

datapath = os.path.join(
    os.path.expanduser("~"), config[dataset]["raw_data"], dataset
)
intermediate_path = os.path.join(
    os.path.expanduser("~"), config[dataset]["intermediate_data"], dataset
)

if not os.path.exists(intermediate_path):
    os.makedirs(intermediate_path)

files = os.listdir(datapath)
parser = lambda date: datetime.strptime(
    date, config[dataset]["datetimeformat"]
)

imo_numbers = []
chunks = []
for file in files:
    filecontent = open(os.path.join(datapath, file))

    df = pd.read_csv(
        filecontent,
        sep=config[dataset]["sep"],
        # chunksize=100000,
        # parse_dates=[config[dataset]["datecol"]],
        # date_parser=parser,
        usecols=["DATE TIME (UTC)", "LONGITUDE", "LATITUDE", "IMO", "SPEED"],
    )

    df.rename(
        columns={
            "DATE TIME (UTC)": "date",
            "LATITUDE": "lat",
            "LONGITUDE": "lon",
            "SPEED": "speed",
            "IMO": "imo",
        },
        inplace=True,
    )

    df.to_csv(
        os.path.join(intermediate_path, file.replace(".csv", "-reduced.csv"))
    )
