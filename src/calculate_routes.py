import functools
import os
import json
import logging

import numpy as np
import pandas as pd
from pandas.tseries.offsets import DateOffset
from shapely.geometry import Point
import geopandas

from helpers import haversine
from sklearn.metrics import mean_squared_error




def create_ship_route(temp_df):
    """ Creates ship route from raw data

    Parameters
    ----------
    temp_df: pd.DataFrame()
        Dataframe with data of one ship

    Returns
    --------
    temp_df: pd.DataFrame()
        Processed dataframe with 5min ship routes
    """
    # select all rows with imo number i
    # if int(i) in [9443566]

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
    temp_df.loc[temp_df["speed"] < 0.1, "speed"] = 0

    temp_df.drop(temp_df.loc[temp_df["tdiff"] < 300].index, inplace=True)

    temp_df.drop(temp_df.loc[temp_df["speed_calc"] > 30].index, inplace=True)

    # set date index
    temp_df = temp_df.set_index("date")

    x = temp_df[(temp_df["tdiff"] > 3600 * 12)]

    # resample to 5min data
    temp_df = temp_df.resample("5min").mean()

    temp_df["tdiff"] = temp_df["tdiff"].fillna(method="ffill")

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

    temp_df.drop(temp_df.loc[temp_df["speed_calc"] > 40].index, inplace=True)

    return temp_df

def calculate_routes(dataset, config):
    """ Calculate the ship routes
    """
    # data path with original intput data
    datapath = os.path.join(
        os.path.expanduser("~"), config["intermediate_data"], dataset, "reduced",
    )

    # path to store data
    intermediate_path = os.path.join(
        os.path.expanduser("~"), config["intermediate_data"], dataset, "ship_routes"
    )

    files = os.listdir(datapath)

    logging.info("Start looping over all files in {}".format(datapath))
    for file in files:
        path = os.path.join(datapath, file)
        logging.info("Read preprocessed file {}".format(file))
        df = pd.read_csv(
            path,
            index_col=0,
            dtype={"IMO": np.int32},
            engine="c",
        )
        df["date"] = pd.to_datetime(df["date"])

        imo_numbers = df["imo"].unique()

        ship_routes = pd.DataFrame()

        logging.info("Loop over ships by IMO number...")

        for i in imo_numbers[1:1000]:
            temp_df = df[df["imo"] == i]
            ship_route = create_ship_route(temp_df)
            ship_routes = pd.concat([ship_routes, ship_route])
        number_nans = ship_routes["speed_calc"].isna().sum()
        ship_routes = ship_routes.dropna(subset=["speed_calc"])
        logging.info("Dropped {} rows with NaN in shiproutes.".format(number_nans))

        logging.info("Calculate RMS for speed.")
        rms = np.sqrt(
            mean_squared_error(ship_routes[["speed"]].fillna(0), ship_routes[["speed_calc"]])
        )
        logging.info("RMS error of speed is {}".format(rms))

        if not os.path.exists(intermediate_path):
            os.makedirs(intermediate_path)
        outputpath = os.path.join(intermediate_path, "ship_routes-" + file)
        logging.info("Write ship routes to {}.".format(outputpath))
        ship_routes.to_csv(outputpath)



# for j in range(1, 32):
#     ship_routes[(ship_routes.index.dayofyear==j)]
#
# # temp_df[temp_df["lon"] == np.nan]
# #
# # ship_routes = ship_routes[(ship_routes.index.dayofyear==1) & (ship_routes.index.hour == 0)]
#
# ship_routes["geometry"] = ship_routes.apply(
#     lambda x: Point((float(x.lon), float(x.lat))), axis=1
# )
# ship_routes = ship_routes.reset_index()
# ship_routes.drop("date", axis=1, inplace=True)
#
# geodf = geopandas.GeoDataFrame(ship_routes, geometry="geometry")
# # proj WGS84
# geodf.crs = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
# geodf.to_file("data/100-200-interpolate.shp", driver="ESRI Shapefile")
