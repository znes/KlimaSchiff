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

# plot for ship age structure
ax = (
    ships.groupby(
        [
            "Class",
            pd.cut(
                ships["BUILT"],
                pd.IntervalIndex.from_tuples(
                    [
                        (0, 1990,),
                        (1990, 1995,),
                        (1995, 2000,),
                        (2000, 2005,),
                        (2005, 2010,),
                        (2010, 2015,),
                        (2015, 2020,),
                    ]
                ),
                precision=0,
            ),
        ]
    )
    .count()["IMO"] # random columns selection to get the count...
    .unstack()
    .plot(kind="barh", stacked=True, cmap=plt.get_cmap("coolwarm_r"))
)
ax.set_ylabel("Number of Ships")
plt.savefig(
    os.path.join(path, "ship_age_by_class.pdf",),
    figsize=(15, 8,),
    bbox_inches="tight",
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
                        (5e3, 25e3,),
                        (25e3, 45e3,),
                        (45e3, 65e3,),
                        (85e3, 100e3,),
                        (100e3, 700e3,),
                    ]
                ),
                precision=0,
            ),
        ]
    )
    .count()["IMO"] # random columns selection to get the count...
    .unstack()
    .plot(kind="bar", stacked=False, cmap=plt.get_cmap("coolwarm"))
)
ax.set_ylabel("Number of Ships")
plt.savefig(
    os.path.join(path, "ship_count_by_class.pdf",),
    figsize=(15, 8,),
    bbox_inches="tight",
)

# ships = ships[ships["GT"] > 0]
# ax = ships['GT'].hist(bins=50, xlabelsize= 10, layout=(3, 3),by=ships['Class'], rot=0)
# for row in ax:
#     for c in row:
#         c.set_yticks(range(0, int(c.get_yticks().max()), int(c.get_yticks().max()/4)))
#
# plt.tight_layout()
# plt.savefig(
#     os.path.join(path, "gt_hist_by_class.pdf",),
#     figsize=(15, 8,),
#     bbox_inches="tight",
# )
