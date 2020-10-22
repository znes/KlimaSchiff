import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

path = os.path.join(os.path.expanduser("~"), "nextcloud-znes", "KlimaSchiff",)

type_mapper = pd.read_excel(
    os.path.join(path, "Ship_Type_Nagel.xlsx",), index_col=0,
)

gt_classes = pd.read_excel(os.path.join(path, "Data", "Ship_Class_Tier.xlsx",), index_col="No")

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

df = pd.DataFrame()
for index in name_mapper:
    cutter = [(float(str(i).split(",")[0]), float(str(i).split(",")[1])) for i in gt_classes.loc[index][["A", "B", "C"]].values]

    ships_by_type = ships[ships["FSGTYPE"]==index]
    classes = ships_by_type.groupby(
        pd.cut(
            ships_by_type["GT"],
            pd.IntervalIndex.from_tuples(
                cutter
            ),
            precision=0,
        )
    ).count()
    classes = classes["GT"].to_frame()
    classes.index = ["A", "B", "C"]
    classes["FSGTYPE"] = index
    classes.set_index("FSGTYPE", append=True, inplace=True)
    df = pd.concat([df, classes])

df = df.unstack(level=0)
df.index = [ name_mapper[i] for i in df.index]
ax = df.plot(kind="bar", stacked=False, cmap=plt.get_cmap("coolwarm"), rot=70)
ax.legend(title="GT class", labels=["A", "B", "C"])
ax.set_ylabel("Number of Ships")
plt.savefig(
    os.path.join(path, "ship_count_by_individual_class.pdf",),
    figsize=(15, 8,),
    bbox_inches="tight",
)

# ----------------------------------------------------------------------------
# for Bulker (4) and Tanker (6) do DWT grouping in seperate plot
# for different ro-ro  also in differnt plot
# DWT plot
df = pd.DataFrame()
for index in name_mapper:#
    if index in [1, 2]:
        cutter = [(0, 25e3), (25e3, 700e3)]#[(0,10e3), (10e3, 25e3), (25e3, 55e3), (55e3, 80e3), (80e3, 85e3),
                 # (85e3, 90e3), (90e3, 95e3), (95e3, 100e3), (100e3, 120e3),
                 # (120e3, 200e3), (200e3, 500e3)]

        ships_by_type = ships[ships["FSGTYPE"]==index]
        classes = ships_by_type.groupby(
            pd.cut(
                ships_by_type["DWT"],
                pd.IntervalIndex.from_tuples(
                    cutter
                ),
                precision=0,
            )
        ).count()
        classes = classes["DWT"].to_frame()
        #classes.index = ["Small Tanker", "Handy Size", "Handy Max", "Pan Max"]
        classes["FSGTYPE"] = index
        classes.set_index("FSGTYPE", append=True, inplace=True)
        df = pd.concat([df, classes])

df = df.unstack(level=0)
df.index = [name_mapper[i] for i in df.index]
ax = df.plot(kind="bar", stacked=False, cmap=plt.get_cmap("coolwarm"), rot=0)
#ax.legend(title="")
ax.set_ylabel("Number of Ships")
plt.savefig(
    os.path.join(path, "bulker_tanker_ship_count_by_DWT_big.pdf",),
    figsize=(15, 8,),
    bbox_inches="tight",
)

# -----------------------------------------------------------------------------
# mean for tankers
df = pd.DataFrame()
for index in name_mapper:#
    if index in [2]:
        cutter = [(0, 25e3), (25e3, 700e3)]#[(0,10e3), (10e3, 25e3), (25e3, 55e3), (55e3, 80e3), (80e3, 85e3),
                 # (85e3, 90e3), (90e3, 95e3), (95e3, 100e3), (100e3, 120e3),
                 # (120e3, 200e3), (200e3, 500e3)]

        ships_by_type = ships[ships["FSGTYPE"]==index]
        classes = ships_by_type.groupby(
            pd.cut(
                ships_by_type["DWT"],
                pd.IntervalIndex.from_tuples(
                    cutter
                ),
                precision=0,
            )
        ).mean()

classes[["GT", "DWT", "LOA", "LPP", "BEAM", "DRAUGHT"]].to_csv(
    os.path.join(path, "roro_passagier_mean_values_by_DWT_classes.csv"))
