import os
import pandas as pd

import matplotlib.pyplot as plt

path = os.path.join(os.path.expanduser("~"), "nextcloud-znes", "KlimaSchiff",)

type_mapper = pd.read_excel(
    os.path.join(path, "Ship_Type_Nagel.xlsx",), index_col=0,
)

name_mapper = pd.read_excel(
    os.path.join(path, "Ship_Type_Nagel.xlsx",),
    sheet_name="FSG_ShipType",
    index_col=0,
).to_dict()["Name ShipType"]

ships = pd.read_csv(
    os.path.join(path, "Data", "VESSELFINDER", "MDB-data-complete-area.csv",)
)


def add_type(row,):
    # import pdb; pdb.set_trace()

    if row["TYPE"] == "0":
        stype = 9
        sname = "Diverse"
    else:
        stype = type_mapper.at[
            row["TYPE"], "FSG No.",
        ]
        sname = name_mapper[stype]

    return (
        stype,
        sname,
    )


ships[["FSGTYPE", "Class",]] = ships.apply(
    add_type, axis=1, result_type="expand",
)

ax = (
    ships.groupby(
        [
            "Class",
            pd.cut(
                ships["GT"],
                pd.IntervalIndex.from_tuples(
                    [
                        (0, 5e3,),
                        (5e3, 30e3,),
                        (40e3, 80e3,),
                        (80e3, 120e3,),
                        (120e3, 160e3,),
                        (160e3, 500e3,),
                    ]
                ),
                precision=0,
            ),
        ]
    )
    .count()["IMO"] # random columns selection to get the count...
    .unstack()
    .plot(kind="bar", stacked=False,)
)
ax.set_ylabel("Number of Ships")
plt.savefig(
    os.path.join(path, "ship_count_by_class.pdf",),
    figsize=(15, 8,),
    bbox_inches="tight",
)

# ax = ships.groupby("Class").count()["IMO"].sort_values().plot(kind="bar", rot=80)
