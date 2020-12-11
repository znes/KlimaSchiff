import os
import json
import logging
from preprocess import preprocess
from calculate_routes import calculate_routes


logging.basicConfig(
    filename=os.path.join(
        os.path.expanduser("~"), "klimaschiff", "klimaschiff.log"
    ),
    level=logging.INFO,
    filemode="w",
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger()
#logger.setLevel(logging.INFO)


logging.info("Start data processing...")
with open("config.json") as file:
    config = json.load(file)

dataset = "vesselfinder"

logging.info("Start preprocessing files for dataset `{}`".format(dataset))
preprocess(dataset, config)

logging.info("Start calculating ship routes.")
calculate_routes(dataset, config)
