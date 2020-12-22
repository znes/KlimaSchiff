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


# Analysis --------------------------------------------------------------------
gt_classes = {
   "RoRo Passenger": [(0, 25e3), (25e3, 700e3)],
   "Cruise Liner": [(0, 25e3), (25e3, float("+inf"))],
   "Diverse": [(0, 2e3), (2e3, float("+inf"))],
   "Cargo": [(0, 50e3), (50e3, 100e3), (100e3, float("+inf"))],
   "Container": [(0, 50e3), (50e3, 100e3), (100e3, float("+inf"))]
   }

dwt_classes = {
    "Bulker": [(0,50e3), (50e3, 100e3),  (100e3, float("+inf"))]
}

df = pd.DataFrame()
for name, cutter in dwt_classes.items():
    ships_by_class = ships[ships["Class"] == name]
    classes = ships_by_class.groupby(
        pd.cut(
            ships_by_class["DWT"],
            pd.IntervalIndex.from_tuples(cutter),
            precision=0,
        )
    ).mean()

    classes[["GT", "DWT", "LOA", "LPP", "BEAM", "DRAUGHT"]].to_csv(
        os.path.join(path, "{}-mean-by-dwt.csv".format(name))
        )
