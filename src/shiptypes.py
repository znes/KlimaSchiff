import os
import pandas as pd
import pickle
import numpy as np
import matplotlib.pyplot as plt

# - data preparation -----------------------------------------------------------
path = os.path.join(os.path.expanduser("~"), "nextcloud-znes", "KlimaSchiff")

type_mapper = pd.read_excel(
    os.path.join(path, "ship_type", "Ship_Type_Nagel.xlsx",), index_col=0,
)

name_mapper = pd.read_excel(
    os.path.join(path, "ship_type", "Ship_Type_Nagel.xlsx",),
    sheet_name="FSG_ShipType",
    index_col=0,
).to_dict()["fsg_name"]

ships = pd.read_csv(
    os.path.join(path, "data", "VESSELFINDER", "MDB-data-complete-area.csv",)
)

# tc (typeclass mapper)
tc_mapper = pd.read_csv(
    os.path.join("emission_model", "ship_weightclass_mapper.csv"),
    index_col=0
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

# extract ships per class and write to pickle
imo_by_type = {}
for index, row in tc_mapper.iterrows():
    imo_by_type[index] = ships[
        (row["class"] == ships["FSGTYPE"]) &
        (row["year"] <= ships["BUILT"]) &
        (ships[row["weighttype"]] > float(row["weightclass"].split(";")[0])) &
        (ships[row["weighttype"]] <= float(row["weightclass"].split(";")[1]))
        ]["IMO"]

with open('emission_model/imo_by_type.pkl', 'wb') as f:
    pickle.dump(imo_by_type, f)
