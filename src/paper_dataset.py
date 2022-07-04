import pickle
import os
from itertools import chain

import pandas as pd
from pathlib import PosixPath

# create path for results
publication_path = os.path.join(
    os.path.expanduser("~"),
    "klimaschiff",
    "publication")

if not os.path.exists(publication_path):
    os.makedirs(publication_path)

# create new unique ids and get imo_by_type dict
p = PosixPath("~/klimaschiff/model_data/imo_by_type_2015.pkl")
with open(p.expanduser(), 'rb') as f:
    imos = pickle.load(f)
imo_list = list(chain.from_iterable(imos.values()))
anonym_id_mapper = dict(zip(imo_list, range(len(imo_list))))

# loop over
p = PosixPath("~/klimaschiff/intermediate_data/2015_sq/ship_emissions")
p = p.expanduser()

droplist = [
    "Propulsion-NPV [EUR]",
    "Electrical-NPV [EUR]",
    "Propulsion-GWP [kg]",
    "Electrical-GWP [kg]",
    "tdiff",
    "dist"
]
def map_imo_type(row):
    return [k for k,v in imos.items() if row["imo"] in v][0]
def map_imo_anonym(row):
    return anonym_id_mapper[row["imo"]]


for file in p.iterdir():
    df = pd.read_csv(file, index_col=0)
    df.drop(droplist, axis=1, inplace=True)
    df.insert(0, "type", df.apply(map_imo_type, axis=1))
    df.insert(0, "unique_id", df.apply(map_imo_anonym, axis=1))
    df.drop("imo", axis=1, inplace=True)
    compression_opts = dict(method='zip',
                            archive_name=file.stem + ".csv")
    df.to_csv(
        os.path.join(publication_path, file.stem + ".zip"),
        index=False,
        compression=compression_opts)
