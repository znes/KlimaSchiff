import os
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def preprocess(dataset, config, debug=False):
    """ Read raw data files for specified dataset and remove obsolete columns, rename
    and write to disk.
    """
    datapath = os.path.join(
        os.path.expanduser("~"), config["raw_data"], dataset
    )
    intermediate_path = os.path.join(
        os.path.expanduser("~"), config["intermediate_data"], dataset, "reduced"
    )

    if not os.path.exists(intermediate_path):
        os.makedirs(intermediate_path)

    files = os.listdir(datapath)

    for file in files:
        filecontent = open(os.path.join(datapath, file))
        logger.info("Read file {}".format(file))
        df = pd.read_csv(
            filecontent,
            sep=config[dataset]["sep"],
            #nrows=20000,
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
        path = os.path.join(intermediate_path, file.replace(".csv", "-reduced.csv"))

        logger.info("Write processed file to {}".format(path))

        df.to_csv(path)
