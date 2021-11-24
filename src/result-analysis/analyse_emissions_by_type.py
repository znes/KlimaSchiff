import json
import pickle
import os
import re
import pandas as pd

with open("config.json") as file:
    config = json.load(file)

imo_by_type = os.path.join(
    os.path.expanduser("~"), config["raw_data"], "imo_by_type.pkl"
)
with open(imo_by_type, "rb") as f:
    ships_per_ship_class = pickle.load(f)

emissions_path = os.path.join(
    os.path.expanduser("~"), config["intermediate_data"], "ship_emissions"
)

files = os.listdir(emissions_path)
files.sort()

emission_by_shiptype = {}
for file in files:
    df = pd.read_csv(os.path.join(emissions_path, file))
    for k, v in ships_per_ship_class.items():
        emission_by_shiptype[(int(re.findall("\d+", file)[0]), k)] = (
            df.loc[df["imo"].isin(v), df.columns[7:25]].sum().values
        )
emissions_by_type_and_day = pd.DataFrame(emission_by_shiptype, index=df.columns[7:25]).T

emissions_by_type_and_day.to_csv(
    os.path.join(
        os.path.expanduser("~"),
        config["result_data"],
    "total_emissions_by_type_and_day.csv")
    )

# df = pd.read_csv("total_emissions_by_type_and_day.csv", index_col=[0,1], parse_dates=True)
# df.groupby(level=1).sum()
