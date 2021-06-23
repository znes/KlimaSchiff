# import functools
import os
import json
import logging
import pickle

import numpy as np
import pandas as pd

# import matplotlib.pyplot as plt
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from scipy import interpolate


def merge_lcpa_models(path="emission_model/lcpa-models"):
    """ merges raw lcpa files
    """
    files = os.listdir(path)
    lcpa = pd.DataFrame()
    for file in files:
        _df = pd.read_csv(
            os.path.join(path, file), sep=";", skiprows=1, index_col=[0]
        )
        lcpa = pd.concat([lcpa, _df])
    lcpa.to_csv("emission_model/lcpa_model.csv", sep=";")
    return lcpa


# merge_lcpa_models()


def append_additional_emissions_to_lcpa():
    """
    """
    df = pd.read_csv(
        "emission_model/lcpa_model.csv", sep=";", index_col=[0, 1]
    )

    max_speed = pd.read_csv("emission_model/max_speed_per_type.csv", index_col=0)

    def _add_emissions(row,):
        """
        """
        energy_factor = row["Energy [J]"] / 3.6e6 / 1e3
        fuel_factor = row["Fuel Consumption [kg]"]  / 1e3

        if row.name[1] == "Electrical":
            bc = 0.15 * energy_factor  # in g/KWh -> kg
            poa = 0.15 * energy_factor
            co = 0.54 * energy_factor
            ash = 0.01 * energy_factor
            nmvoc = 1.8 * fuel_factor
        else:
            bc = 0.03 * energy_factor
            poa = 0.01 * energy_factor
            co = 0.54 * energy_factor
            ash = 0.01 * energy_factor

            if any(i in row.name[0] for i in ["Bulker", "Tanker", "Container", "Cargo"]):
                if row["Speed [m/second]"] > (0.5 * max_speed.loc[row.name[0]].values[0]):
                    nmvoc = 3.2 * fuel_factor
                else:
                    nmvoc = 8.6 * fuel_factor # cruise mode
            else:
                if row["Speed [m/second]"] > (0.35 * max_speed.loc[row.name[0]].values[0]):
                    nmvoc = 2.3 * fuel_factor
                else:
                    nmvoc = 6.6 * fuel_factor

        return (bc, ash, poa, co, nmvoc)

    df[
        [
            "BC [kg]",
            "ASH [kg]",
            "POA [kg]",
            "CO [kg]",
            "NMVOC [kg]"
        ]
    ] = df.apply(_add_emissions, axis=1, result_type="expand",)

    df.to_csv("emission_model/model.csv", sep=";")
#append_additional_emissions_to_lcpa()

#df = pd.read_csv("emission_model/model.csv", sep=";", index_col=[0,1])
#df.groupby(level=0).apply(max)["Speed [m/second]"].to_csv("emission_model/max_speed_per_type.csv")

def create_model(
    model_data,
    ship_class="Tanker_Handy_Max_Tier_II",
    emission_type="CO2 (Well to tank) [kg]",
    interpolate_values=True,
    engine=None,
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
    engine: str
        Which engine should be used one of "Electrical" and "Propulsion"

    Returns
    -------
    fit
    """

    if interpolate_values is True:
        model = interpolate(
            model_data.loc[(ship_class, engine)]["Speed [m/second]"],
            model_data.loc[(ship_class, engine)][emission_type],
            fill_value="extrapolate",
        )
    else:
        x = model_data.loc[(ship_class, engine)]["Speed [m/second]"]
        y = model_data.loc[(ship_class, engine)][emission_type]
        X = x[:, np.newaxis]
        model = make_pipeline(PolynomialFeatures(degree=3), Ridge())
        model.fit(X, y)

    return model


def create_models(model_data, emission_types=None):
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
        emission_types = model_data.columns[2:]
    models = {
        (ship_class, engine, emission_type): create_model(
            model_data, ship_class, emission_type, engine
        )
        for emission_type in emission_types
        for ship_class, engine in model_data.index.unique()
    }

    return models


def interpolate_emissions(
    routes,
    emission_types,
    ship_classes,
    engine_types,
    ships_per_ship_class,
    model_data,
    resample,
):
    """ Much simpler way of the fitting solution in "emissions_by_type_and_class()"
    to get emissions
    """
    emissions = {}
    for ship_class in ship_classes:

        # TODO: Check if ship_class exists if not log warning!
        ship_imo_numbers = ships_per_ship_class[ship_class]
        x = routes.loc[routes["imo"].isin(ship_imo_numbers)]

        if not x.empty:
            for emission_type in emission_types:
                for engine in engine_types:
                    # import pdb;pdb.set_trace()
                    x.loc[:, (engine + "-" + emission_type)] = np.interp(
                        x["speed_calc"],
                        model_data.loc[(ship_class, engine)][
                            "Speed [m/second]"
                        ].values,
                        model_data.loc[(ship_class, engine)][
                            emission_type
                        ].values,
                    ) / (
                        60 / int(resample)
                    )  # convert from hourly values to "resample" minutes
            emissions[ship_class] = x
        else:
            emissions[ship_class] = None
    return emissions


def emissions_by_type_and_class(
    routes,
    emission_types,
    ship_classes,
    engine_types,
    ships_per_ship_class,
    models,
    resample,
):
    """
    """
    emissions = {}
    for ship_class in ship_classes:

        # TODO: Check if ship_class exists if not log warning!
        ship_imo_numbers = ships_per_ship_class[ship_class]
        x = routes.loc[routes["imo"].isin(ship_imo_numbers)]

        if not x.empty:
            for emission_type in emission_types:
                for engine in engine_types:
                    x.loc[:, (engine, emission_type)] = models[
                        (ship_class, engine, emission_type)
                    ](
                        x["speed_calc"]
                    )  # .predict(x["speed_calc"][:, np.newaxis]) / ( 60 / int(resample) ) # convert from hourly values to "resample" minutes
            emissions[ship_class] = x
        else:
            emissions[ship_class] = None
    return emissions


def read_routes(filepath):
    """
    """
    routes = pd.read_csv(filepath)  # usecols=["imo", "speed_calc"]
    nans = routes.imo.isna().sum()
    if nans > 0:
        logging.warning(
            "`{}` NANs in ships routes removed from file: `{}`".format(
                nans, filepath
            )
        )
    routes = routes.dropna(how="any")
    routes["imo"] = routes.imo.astype("int")
    return routes


def test_models():
    """
    """
    model_data = pd.read_csv(
        "emission_model/model.csv", sep=";", index_col=[0]
    )

    models = create_models(model_data)

    predicted = {}
    for i in models:
        # if i[1] == "NOx [kg]":
        predicted[i] = models[i].predict(
            np.reshape(np.linspace(0, 15, 150), (150, 1))
        )
    df = pd.DataFrame(predicted).stack(level=0)
    df.index = df.index.swaplevel()
    df = df.sort_index()

    df.to_csv("emission_model/predicted-new.csv")


# test_models()


def calculate_emissions(
    config, columns=["Fuel Consumption [kg]", "NOx [kg]", "CO2 [kg]"]
):
    """
    """

    # with open("config.json") as file:
    #     config = json.load(file)
    datapath = os.path.join(
        os.path.expanduser("~"), config["intermediate_data"], "ship_routes"
    )

    outputpath = os.path.join(
        os.path.expanduser("~"), config["intermediate_data"], "ship_emissions"
    )

    if not os.path.exists(outputpath):
        os.makedirs(outputpath)

    filepaths = [os.path.join(datapath, i) for i in os.listdir(datapath)]

    # get gict with mapper for imo-number to model
    with open("emission_model/imo_by_type.pkl", "rb") as f:
        ships_per_ship_class = pickle.load(f)

    model_data = pd.read_csv(
        "emission_model/model.csv", sep=";", index_col=[0, 1]
    )

    for filepath in filepaths:
        routes = read_routes(filepath)

        emissions = interpolate_emissions(
            routes,
            ship_classes=[
                i
                for i in model_data.index.get_level_values(0).unique()
                if not " FS" in i
            ],
            engine_types=[
                i for i in model_data.index.get_level_values(1).unique()
            ],  # ["Electrical", "Propulsion"]
            emission_types=[
                "SOx [kg]",
                "PM [kg]",
                "NOx [kg]",
                "CO2 [kg]",
                "BC [kg]",
                "ASH [kg]",
                "POA [kg]",
                "CO [kg]",
                "NMVOC [kg]"
            ],
            ships_per_ship_class=ships_per_ship_class,
            model_data=model_data,
            resample=config["resample"],
        )
        model_data.index.get_level_values(0).unique()
        outputfile = os.path.join(
            outputpath,
            os.path.basename(filepath).replace(
                "ship_routes", "ship_emissions"
            ),
        )
        pd.concat(emissions.values()).sort_index().to_csv(
            outputfile, index=False
        )
