#import functools
import os
import json
import logging
import pickle

import numpy as np
import pandas as pd

#import matplotlib.pyplot as plt
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline


def merge_lcpa_models(path="emission_model/lcpa-models"):
    """ merges raw lcpa files
    """
    files = os.listdir(path)
    lcpa = pd.DataFrame()
    for file in files:
        _df = pd.read_csv(
            os.path.join(path, file),
            sep=";", skiprows=1, index_col=[0])
        lcpa = pd.concat([lcpa, _df])
    lcpa.to_csv("emission_model/model.csv", sep=";")
    return lcpa
#merge_lcpa_models()


def create_model(
    model_data,
    ship_class="Tanker_Handy_Max_Tier_II",
    emission_type="CO2 (Well to tank) [kg]",
    ):
    """ Create a speed-emission model (fit) for a ship class and a specific
    emission based on LCPA data

    Parameters
    -----------
    model_data: pd.DataFrame
        DF containing the LCPA results for the different ship classes
    ships_class: str
        Name of ship class, must be in index of `model_data`
    emission_type: str
        Emission, must be in column of `model_data`

    Returns
    -------
    fit
    """

    x = model_data.loc[ship_class]["Speed [m/second]"]
    y = model_data.loc[ship_class][emission_type]
    X = x[:, np.newaxis]
    model = make_pipeline(PolynomialFeatures(degree=5), Ridge())
    model.fit(X, y)

    return model


def create_models(model_data, emission_types):
    """ Creates all models for all ship classes in model data and all
    emission_types provided.

    Parameters
    -----------
    model_data: pd.DataFrame
        s. create model
    emissions_types: list
        list with names of emissions (string) which are `model_data` columns
        If is None, columns for 2:end from `model_data` are used 

    Returns
    -------
    Dict with tuple keys (ship_class, emission_type) and values fit model for
    all shipclasses and emission types (columns!)
    """
    if emission_types is None:
        emission_types=model_data.columns[2:]
    models = {
        (ship_class, emission_type): create_model(model_data, ship_class, emission_type)
        for emission_type in emission_types
        for ship_class in model_data.index.unique()
    }

    return models


# def fit_emissions(model):
#      model.predict(
#         x[:, np.newaxis]
#     )
#     return None


def emissions_by_type(
    routes, emission_type, ship_classes, ships_per_ship_class, models):
    """
    """
    for ship_class in ship_classes:
        ship_imo_numbers = ships_per_ship_class[ship_class]
        x = routes.loc[routes["imo"].isin(ship_imo_numbers)]
        routes[emission_type] = models[(ship_class, emission_type)].predict(
            x[:, np.newaxis]
        )
    return routes


def read_routes(filepath):
    routes = pd.read_csv(filepath, usecols=["imo", "speed_calc"])
    nans =routes.imo.isna().sum()
    if nans > 0:
        logging.warning("`{}` NANs in ships routes removed from file: `{}`".format(nans, filepath))
    routes = routes.dropna(how="any")
    routes["imo"]  = routes.imo.astype("int")
    return routes



#----------------- workflow

# get  path of files with routes
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

# get gict with mapper for imo-number to model
with open('emission_model/imo_by_type.pkl', 'rb') as f:
    ships_per_ship_class = pickle.load(f)

model_data = pd.read_csv(
         "emission_model/model.csv", sep=";", index_col=[0]
     )

models = create_models(model_data)

routes = read_routes(filepaths[0])

emissions = emissions_by_type(routes,
                  ship_classes=["Tanker_Handy_Max_Tier_II"],
                  emission_type="CO2 (Well to tank) [kg]",
                  ships_per_ship_class=ships_per_ship_class,
                  models=models)

#
#
# import time
# start = time.process_time()
# elapsed_time = time.process_time() - start

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
#     )
#         )
