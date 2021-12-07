import os
import logging
import pickle

import pandas as pd

logger = logging.getLogger(__name__)


def reduce_ais_data(dataset, config, debug=False):
    """ Read raw data files for specified dataset and remove obsolete columns, rename
    and write to disk.
    """

    datapath = os.path.join(
        os.path.expanduser("~"), config["raw_data"], dataset
    )
    processed_path = os.path.join(os.path.expanduser("~"), config["processed"])

    if not os.path.exists(processed_path):
        os.makedirs(processed_path)

    files = os.listdir(datapath)

    for file in files:
        logger.info("Read and reduce dataset `{}`".format(file))
        filepath = os.path.join(datapath, file)
        filecontent = open(filepath)
        df = pd.read_csv(
            filecontent,
            index_col=0,
            sep=config[dataset]["sep"],
            # nrows=20000,
            usecols=config[dataset]["columns"].keys(),
        )
        df.index = pd.to_datetime(
            df.index, format=config[dataset]["datetimeformat"]
        ).strftime("%Y-%m-%d %H:%M:%S")

        df.index.name = "datetime"

        df.rename(
            columns=config[dataset]["columns"], inplace=True,
        )
        path = os.path.join(
            processed_path, file.replace(".csv", "-reduced.csv")
        )

        logger.info("Write processed file to {}".format(path))

        df.to_csv(path)


def merge_ais_data(config):
    """
    """
    datapath = os.path.join(os.path.expanduser("~"), config["processed"])

    months = ["201412"] + [str(2015) + str(i).zfill(2) for i in range(1, 13)]

    for month in months:
        logging.info("Merge month {}".format(str(month)))
        vessel_file = os.path.join(
            datapath, "vesselfinder_" + month + "-reduced.csv"
        )
        helcom_file = os.path.join(
            datapath, "helcom_" + month + "-reduced.csv"
        )

        vessel_df = pd.read_csv(
            vessel_file,
            index_col=[0],
            # nrows=10000000,
            parse_dates=True,
        )
        helcom_df = pd.read_csv(
            helcom_file,
            index_col=[0],
            # nrows=10000000,
            parse_dates=True,
        )

        # first write vesselfinder
        merged_dirpath = os.path.join(
            os.path.expanduser("~"), config["merged"]
        )
        if not os.path.exists(merged_dirpath):
            os.makedirs(merged_dirpath)

        for day in vessel_df.index.day.unique():
            logging.info("Writing merged data for day {}".format(day))
            merged_filepath = os.path.join(
                merged_dirpath, month + str(day).zfill(2) + ".csv"
            )

            vessel_df.loc[vessel_df.index.day == day].to_csv(merged_filepath)

            helcom_day = helcom_df.loc[helcom_df.index.day == day]

            helcom_day[helcom_day["lon"] > vessel_df["lon"].max()].to_csv(
                merged_filepath, mode="a", header=False
            )


def merge_lcpa_models(
    input_path=os.path.join("emission_model", "lcpa-models"),
    output_path=os.path.join("emission_model", "lcpa_model.csv"),
):
    """ Merges raw lcpa files
    """
    logger.info(
        "Merging lcpa models from {0} to one file {1}".format(
            input_path, output_path
        )
    )

    files = os.listdir(input_path)
    lcpa = pd.DataFrame()
    for file in files:
        _df = pd.read_csv(
            os.path.join(input_path, file), sep=";", skiprows=1, index_col=[0]
        )
        lcpa = pd.concat([lcpa, _df])

    lcpa.to_csv(output_path, sep=";")

    return lcpa


def append_additional_emissions_to_lcpa(
    scenario="2015_sq",
    lcpa_model_path=os.path.join("emission_model", "lcpa_model.csv"),
    max_speed_path=os.path.join("emission_model", "max_speed_per_type.csv"),
    output_dir=None,
):
    """
    """

    # read the lcpa model to extend be additional pollutants
    df = pd.read_csv(lcpa_model_path, sep=";", index_col=[0, 1])

    # get the maximum speed per shiptype
    # created by code:
    # df = pd.read_csv("emission_model/model.csv", sep=";", index_col=[0,1])
    # df.groupby(level=0).apply(max)["Speed [m/second]"].to_csv("emission_model/max_speed_per_type.csv")

    max_speed = pd.read_csv(max_speed_path, index_col=0)

    def _add_emissions(row, scenario):
        """
        """
        energy_factor = row["Energy [J]"] / 3.6e6 / 1e3
        fuel_factor = row["Fuel Consumption [kg]"] / 1e3

        # for future scenarios apply different emission factors
        if "FS" in row.name[0] and "low" in scenario:
            bc = 0
            poa = 0
            co = 0
            ash = 0
            nmvoc = 0

            return (bc, ash, poa, co, nmvoc)

        elif "FS" in row.name[0] and "high" in scenario:
            # for "high" future scenario 0 for black carbon and ash,
            # rest like SQ

            bc = 0
            ash = 0

            if row.name[1] == "Electrical":
                poa = 0.15 * energy_factor
                co = 0.54 * energy_factor
                nmvoc = 0.4 * energy_factor
            else:
                poa = 0.2 * energy_factor
                co = 0.54 * energy_factor

                if any(
                    i in row.name[0]
                    for i in ["Bulker", "Tanker", "Container", "Cargo", "MPV"]
                ):
                    if row["Speed [m/second]"] > (
                        0.5 * max_speed.loc[row.name[0]].values[0]
                    ):
                        nmvoc = 0.6 * energy_factor  # cruise mode
                    else:
                        nmvoc = 1.8 * energy_factor  # hotelling
                else:
                    if row["Speed [m/second]"] > (
                        0.35 * max_speed.loc[row.name[0]].values[0]
                    ):
                        nmvoc = 0.5 * energy_factor
                    else:
                        nmvoc = 1.5 * energy_factor

            return (bc, ash, poa, co, nmvoc)

        elif "sq" in scenario:
            if row.name[1] == "Electrical":
                bc = 0.15 * energy_factor  # in g/KWh -> kg
                poa = 0.15 * energy_factor
                co = 0.54 * energy_factor
                ash = 0.02 * 0.001 * fuel_factor
                nmvoc = 0.4 * energy_factor
            else:
                bc = 0.03 * energy_factor
                poa = 0.2 * energy_factor
                co = 0.54 * energy_factor
                ash = 0.02 * 0.001 * fuel_factor

                if any(
                    i in row.name[0]
                    for i in ["Bulker", "Tanker", "Container", "Cargo", "MPV"]
                ):
                    if row["Speed [m/second]"] > (
                        0.5 * max_speed.loc[row.name[0]].values[0]
                    ):
                        nmvoc = 0.6 * energy_factor  # cruise mode
                    else:
                        nmvoc = 1.8 * energy_factor  # hotelling
                else:
                    if row["Speed [m/second]"] > (
                        0.35 * max_speed.loc[row.name[0]].values[0]
                    ):
                        nmvoc = 0.5 * energy_factor
                    else:
                        nmvoc = 1.5 * energy_factor

            return (bc, ash, poa, co, nmvoc)
        else:
            pass

    df[
        ["BC [kg]", "ASH [kg]", "POA [kg]", "CO [kg]", "NMVOC [kg]"]
    ] = df.apply(
        _add_emissions, axis=1, result_type="expand", scenario=scenario
    )

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    df.to_csv(os.path.join(output_dir, "model_" + scenario + ".csv"), sep=";")


def create_ship_dataframe():
    type_mapper = pd.read_excel(
        os.path.join("emission_model", "ship_type_fsg_mdb_mapper.xlsx"),
        index_col=0,
    )

    name_mapper = pd.read_excel(
        os.path.join("emission_model", "ship_type_fsg_mdb_mapper.xlsx"),
        sheet_name="FSG_ShipType",
        index_col=0,
    ).to_dict()["fsg_name"]

    ships = pd.read_csv(
        os.path.join(
            os.path.expanduser("~"),
            "klimaschiff",
            "raw_data",
            "MDB-data-complete-area.csv",
        )
    )

    def add_type(row,):
        # import pdb; pdb.set_trace()
        if row["TYPE"] == "0":
            stype = 9
            sname = "Diverse"
        else:
            stype = type_mapper.at[
                row["TYPE"], "fsg_no",
            ]
            sname = name_mapper[stype]

        return (
            stype,
            sname,
        )

    ships[["FSGTYPE", "Class",]] = ships.apply(
        add_type, axis=1, result_type="expand",
    )
    ships = ships.drop(ships.loc[ships["Class"] == "rausnehmen"].index, axis=0)

    return ships


def build_imo_lists(config):
    """ Hackisch function to create listes with ships types and corresponding
    list of imo numbers depend on scenario year


    """
    ships = create_ship_dataframe()
    # tc (typeclass mapper)
    tc_mapper = pd.read_csv(
        os.path.join("emission_model", "ship_weightclass_mapper.csv"),
        index_col=0,
    )
    # ships[(ships["BUILT"] != 0) & (ships["STATUS"] == "IN SERVICE/COMMISSION")].min()

    # extract ships per class and write to pickle
    imo_by_type = {}
    for index, row in tc_mapper.iterrows():
        if not " FS" in index:
            imo_by_type[index] = [
                i
                for i in ships[
                    (row["class"] == ships["FSGTYPE"])
                    & (ships["BUILT"] >= float(row["year_lb"]))
                    & (ships["BUILT"] <= float(row["year_ub"]))
                    & (
                        ships[row["weighttype"]]
                        >= float(row["weightclass_lb"])
                    )
                    & (
                        ships[row["weighttype"]]
                        <= float(row["weightclass_ub"])
                    )
                ]["IMO"]
                .to_dict()
                .values()
            ]

    # write the detailled type to the ship DB
    ships["DETAILTYPE"] = None
    for k, v in imo_by_type.items():
        ships.loc[ships[ships["IMO"].isin(v)].index, "DETAILTYPE"] = k

    # create scenarios
    ships_2030 = ships.copy()
    ships_2040 = ships.copy()
    ships_2050 = ships.copy()

    def append_future_suffix(row, year):
        if row["BUILT"] < year:
            return row["DETAILTYPE"] + " FS"
        else:
            return row["DETAILTYPE"]

    ships_2030["DETAILTYPE"] = ships_2030.apply(
        append_future_suffix, axis=1, year=2005
    )
    ships_2040["DETAILTYPE"] = ships_2040.apply(
        append_future_suffix, axis=1, year=2015
    )
    ships_2050["DETAILTYPE"] = ships_2050.apply(
        append_future_suffix, axis=1, year=2025
    )

    # convert to lists for correct type
    imo_by_type_2030 = {}
    for k, v in (
        ships_2030.set_index("IMO").groupby("DETAILTYPE").groups.items()
    ):
        imo_by_type_2030[k] = v.tolist()

    imo_by_type_2040 = {}
    for k, v in (
        ships_2040.set_index("IMO").groupby("DETAILTYPE").groups.items()
    ):
        imo_by_type_2040[k] = v.tolist()

    imo_by_type_2050 = {}
    for k, v in (
        ships_2050.set_index("IMO").groupby("DETAILTYPE").groups.items()
    ):
        imo_by_type_2050[k] = v.tolist()

    # flat_ls = []
    # for i in imo_by_type_2030.values():
    #     for j in i:
    #         flat_ls.append(j)

    # for manual testing:
    # ships[ships["IMO"] == imo_by_type["Car_Carrier_groesser_40000_GT__Tier_II"][4]]
    if config is None:
        with open("config.json") as file:
            config = json.load(file)

    imo_path = os.path.join(os.path.expanduser("~"), config["model_data"])
    with open(os.path.join(imo_path, "imo_by_type_2015_sq.pkl"), "wb") as f:
        pickle.dump(imo_by_type, f)
    with open(os.path.join(imo_path, "imo_by_type_2030_fs.pkl"), "wb") as f:
        pickle.dump(imo_by_type_2030, f)
    with open(os.path.join(imo_path, "imo_by_type_2040_fs.pkl"), "wb") as f:
        pickle.dump(imo_by_type_2040, f)
    with open(os.path.join(imo_path, "imo_by_type_2050_fs.pkl"), "wb") as f:
        pickle.dump(imo_by_type_2050, f)


if __name__ == "__main__":

    import json
    from logger import logger

    logging.info("Start data pre processing...")

    with open("config.json") as file:
        config = json.load(file)

    datasets = ["vesselfinder", "helcom"]
    #
    for d in datasets:
        reduce_ais_data(d, config)

    merge_ais_data(config)
