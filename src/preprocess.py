import os
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def reduce(dataset, config, debug=False):
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
        filepath = os.path.join(datapath, file)
        filecontent = open(filepath)
        logger.info("Read file {}".format(filepath))
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


def merge(config):
    """
    """
    datapath = os.path.join(os.path.expanduser("~"), config["processed"])

    months = [str(i).zfill(2) for i in range(1, 2)]

    for month in months:
        logging.info("Merge month {}".format(str(months)))
        vessel_file = os.path.join(
            datapath, "vesselfinder_2015" + month + "-reduced.csv"
        )
        helcom_file = os.path.join(
            datapath, "helcom_2015" + month + "-reduced.csv"
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
                merged_dirpath, "2015" + month + str(day).zfill(2) + ".csv"
            )

            vessel_df.loc[vessel_df.index.day == day].to_csv(merged_filepath)

            helcom_day = helcom_df.loc[helcom_df.index.day == day]

            helcom_day[helcom_day["lon"] > vessel_df["lon"].max()].to_csv(
                merged_filepath, mode="a", header=False
            )


if __name__ == "__main__":

    import json
    from logger import logger

    logging.info("Start data processing...")

    with open("config.json") as file:
        config = json.load(file)

    datasets = ["vesselfinder", "helcom"]
    #
    for d in datasets:
        logging.info("Start preprocessing files for dataset `{}`".format(d))
        reduce(d, config)

    merge(config)
