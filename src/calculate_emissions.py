import functools
import os
import json
import logging
import pickle

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline


# ax = plt.plot(x, y_plot, linewidth=2,color="red")
# plt.scatter(x, y, marker="o")
def create_model(
    ship_class="Tanker_Handy_Max_Tier_II",
    emission_type="CO2 (Well to tank) [kg]",
    model_data):

    x = model_data.loc[ship_class]["Speed [m/second]"]
    y = model_data.loc[ship_class][emission_type]
    X = x[:, np.newaxis]
    model = make_pipeline(PolynomialFeatures(degree=5), Ridge())
    model.fit(X, y)

    return model


def create_models(model_data):
    models = {
        (ship_class, emission_type): create_model(ship_class, emission_type, model_data)
        for emission_type in model_data.columns[2:]
        for ship_class in model_data.index.unique()
    }

    return models


def emissions_by_type(
    filepath, emission_type, ship_classes, ships_per_ship_class, models):
    """
    """
    df = pd.read_csv(filepath, usecols=["imo", "speed_calc"])

    for ship_class in ship_classes:
        ship_imo_numbers = ships_per_ship_class[ship_class]
        x = df.loc[(df["imo"] in ship_imo_numbers)]
        df[emission_type] = models[(ship_class, emission_type)].predict(
            x[:, np.newaxis]
        )
    return df


dataset = "vesselfinder"
with open("config.json") as file:
    config = json.load(file)
datapath = os.path.join(
    os.path.expanduser("~"),
    config["intermediate_data"],
    dataset,
    "ship_routes"
)

filepaths = [os.path.join(datapath, i) for i in os.listdir(datapath)]

with open('emission_model/imo_by_type.pkl', 'rb') as f:
    ships_per_ship_class = pickle.load(f)

emissions_by_type(filepaths[0],
                  ship_classes=["Tanker_Handy_Max_Tier_II"],
                  emission_type="CO2 (Well to tank) [kg]")

import time
start = time.process_time()
elapsed_time = time.process_time() - start


# def create_emission_model_table():
#     # read model and create ship / interval-index for lookup
#     logging.info("Create lookup emission model file")
#     model_table = pd.read_csv(
#         "emission_model/test-model.csv", sep=";", skiprows=1, index_col=[0]
#     )
#
#     index = pd.IntervalIndex.from_arrays(
#         left=model_table.iloc[0:101]["Speed [m/second]"].values,
#         right=model_table.iloc[0:101]
#         .shift(-1)["Speed [m/second]"]
#         .fillna(50)
#         .values,
#         closed="left",
#     )
#     multiindex = pd.MultiIndex.from_product(
#         [model_table.index.unique(), index], names=["type", "v_class"]
#     )
#     model_table = model_table.set_index(multiindex)
#
#     return model_table
# def emission_model(model_table, ship_type, emission_type, row):
#     """ Function for pandas rowwise apply look-up
#     """
#     if ship_type is None:
#         raise ValueError("Missing ship_type!")
#     if emission_type is None:
#         raise ValueError("Missing emission type!")
#
#     try:
#         return  model_table.loc[ship_type].loc[row][emission_type]
#     except KeyError:
#         logging.error("Key error in emission model with row: {}".format(row))
#         return np.nan
#
# def calc_emission(temp_df, model_table):
#     # look up emissions (TODO: replace with function)
#     temp_df["emission"] = temp_df["speed_calc"].apply(
#         functools.partial(
#             emission_model,
#             model_table,
#             "Tanker_Handy_Max_Tier_II",
#             "CO2 (Well to tank) [kg]",
#         )
#     )
