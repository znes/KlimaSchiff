import os

import pandas as pd
import numpy as np

from src.preprocess import create_ship_dataframe

ships = create_ship_dataframe()

imos = ships.IMO.unique()

files = os.listdir(os.path.join(
    os.path.expanduser("~"),
    "klimaschiff",
    "raw_data",
    "processed"))

l = []
for file in files:
    if file.endswith(".csv"):
        df = pd.read_csv(
            os.path.join(
                os.path.expanduser("~"),
                "klimaschiff",
                "raw_data",
                "processed",
                file
                ), nrows=10000
            )

        month = df.imo.unique()

        len([i for i in np.isin(month, imos) if i==True]) / len(month)
        mask = np.isin(month, imos)
        number, share = len(month), (1 - len(month[mask]) / len(month)) * 100

        l.append((file, number, share))

df = pd.DataFrame(l, columns=["File", "Unique_imos", "Not in"])
df.to_csv("imo_in_MDB_check.csv")
