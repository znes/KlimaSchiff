import functools
import os
import json

import numpy as np
import pandas as pd
from pandas.tseries.offsets import DateOffset
from shapely.geometry import Point
import geopandas

from src.helpers import haversine
from sklearn.metrics import mean_squared_error

dataset = "vesselfinder"

with open("config.json") as file:
    config = json.load(file)

# data path with original intput data
datapath = os.path.join(
    os.path.expanduser("~"), config["intermediate_data"]
)

# path to store data
intermediate_path = os.path.join(
    os.path.expanduser("~"), config["intermediate_data"]
)

df = pd.read_csv(
    os.path.join(datapath, "vesselfinder_201501-reduced.csv"),
    index_col=0,
    dtype={"IMO": np.int32},
    engine="c",
)

df["DATE TIME (UTC)"] = pd.to_datetime(df["DATE TIME (UTC)"])

imo_numbers = df["IMO"].unique()

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


# read model and create ship / interval-index for lookup
model_table = pd.read_csv(
    "emission_model/test-model.csv", sep=";", skiprows=1, index_col=[0]
)

index = pd.IntervalIndex.from_arrays(
    left=model_table.iloc[0:101]["Speed [m/second]"].values,
    right=model_table.iloc[0:101]
    .shift(-1)["Speed [m/second]"]
    .fillna(40)
    .values,
    closed="left",
)
multiindex = pd.MultiIndex.from_product(
    [model_table.index.unique(), index], names=["type", "v_class"]
)
model_table = model_table.set_index(multiindex)


def emission_model(ship_type, emission_type, row):
    """
    """
    if ship_type is None:
        raise ValueError("Missing ship_type!")
    if emission_type is None:
        raise ValueError("Missing emission type!")

    return model_table.loc[ship_type].loc[row][emission_type]


ship_routes = pd.DataFrame()
for i in imo_numbers[0:100]:
    # select all rows with imo number i
    # if int(i) in [9443566]:
    temp_df = df[df["imo"] == i]

    # sort values by time
    temp_df = temp_df.sort_values(by="date", ascending=True)

    # calculate distance between two points of  consecutive timesteps in m
    temp_df["dist"] = (
        haversine(
            temp_df.lat.shift(),
            temp_df.lon.shift(),
            temp_df["lat"],
            temp_df["lon"],
        )
        * 1000
    )

    # get time in seconds
    temp_df["tdiff"] = temp_df["date"].diff().dt.total_seconds()

    # calculate avg. speed based on distance an time-diff in m/s
    temp_df["speed_calc"] = temp_df["dist"] / temp_df["tdiff"]

    # temp_df["dist"] = temp_df["dist"].shift(-1)
    temp_df.dropna(inplace=True)

    # set speed to 0 where speed is lower that 0.1 m/s
    temp_df["speed"][temp_df["speed"] < 0.1] = 0

    temp_df.drop(temp_df.loc[temp_df["tdiff"] < 300].index, inplace=True)

    temp_df.drop(temp_df.loc[temp_df["speed_calc"] > 30].index, inplace=True)

    # set date index
    temp_df = temp_df.set_index("date")

    x = temp_df[(temp_df["tdiff"] > 3600 * 12)]

    temp_df.to_csv("raw.csv")

    # resample to 5min data
    temp_df = temp_df.resample("5min").mean()

    temp_df["tdiff"] = temp_df["tdiff"].fillna(method="ffill")
    temp_df.to_csv("resampled.csv")
    x = temp_df[
        (temp_df["tdiff"] > 3600 * 24)  # maximum 1 hour to interpolate
        | (
            (temp_df["tdiff"] > 300)  # or 300 m at the outer area
            & (
                (temp_df["lon"] < -4.9) | (temp_df["lon"] > 14.9)
            )  # clip geo-bounds
        )
    ]

    for k in x.index:
        temp_df.drop(
            temp_df.loc[
                k - DateOffset(seconds=x.loc[k]["tdiff"] - (5 * 60)) : k
            ].index,
            inplace=True,
        )

    # interpolate lon/lat to get the positions of the ships
    temp_df[["lon", "lat"]] = temp_df[["lon", "lat"]].interpolate()

    # create speed for resample data
    temp_df[["speed_calc", "imo"]] = temp_df[["speed", "imo"]].fillna(
        method="ffill"
    )
    temp_df.to_csv("interpolate.csv")

    # look up emissions (TODO: replace with function)
    temp_df["emission"] = temp_df["speed_calc"].apply(
        functools.partial(
            emission_model,
            "Tanker_Handy_Max_Tier_II",
            "CO2 (Well to tank) [kg]",
        )
    )

    ship_routes = pd.concat([ship_routes, temp_df])


rms = np.sqrt(
    mean_squared_error(ship_routes[["speed"]].fillna(0), ship_routes[["speed_calc"]])
)

ship_routes.to_csv(os.path.join(intermediate_path, "ship_routes.csv"))

# for i in range(1,32):
#     ship_routes[ship_routes.index.dayofyear==i]
# temp_df[temp_df["lon"] == np.nan]
#
# ship_routes = ship_routes[(ship_routes.index.dayofyear==1) & (ship_routes.index.hour == 0)]

ship_routes["geometry"] = ship_routes.apply(
    lambda x: Point((float(x.lon), float(x.lat))), axis=1
)
ship_routes = ship_routes.reset_index()
ship_routes.drop("date", axis=1, inplace=True)

geodf = geopandas.GeoDataFrame(ship_routes, geometry="geometry")
# proj WGS84
geodf.crs = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
geodf.to_file("data/100-200-interpolate.shp", driver="ESRI Shapefile")
