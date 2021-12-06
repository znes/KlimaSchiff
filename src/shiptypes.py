import os
import pandas as pd
import pickle
import json



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

ships = create_ship_dataframe()
# tc (typeclass mapper)
tc_mapper = pd.read_csv(
    os.path.join("emission_model", "ship_weightclass_mapper.csv"), index_col=0
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
                & (ships[row["weighttype"]] >= float(row["weightclass_lb"]))
                & (ships[row["weighttype"]] <= float(row["weightclass_ub"]))
            ]["IMO"]
            .to_dict()
            .values()
        ]

# write the detailled type to the ship DB
ships["DETAILTYPE"] = None
for k,v in imo_by_type.items():
    ships.loc[ships[ships['IMO'].isin(v)].index, "DETAILTYPE"] = k

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
for k,v in ships_2030.set_index("IMO").groupby("DETAILTYPE").groups.items():
    imo_by_type_2030[k] = v.tolist()

imo_by_type_2040 = {}
for k,v in ships_2040.set_index("IMO").groupby("DETAILTYPE").groups.items():
    imo_by_type_2040[k] = v.tolist()

imo_by_type_2050 = {}
for k,v in ships_2050.set_index("IMO").groupby("DETAILTYPE").groups.items():
    imo_by_type_2050[k] = v.tolist()

# flat_ls = []
# for i in imo_by_type_2030.values():
#     for j in i:
#         flat_ls.append(j)

# for manual testing:
# ships[ships["IMO"] == imo_by_type["Car_Carrier_groesser_40000_GT__Tier_II"][4]]
with open("config.json") as file:
    config = json.load(file)

imo_path = os.path.join(
    os.path.expanduser("~"),
    "klimaschiff",
    "raw_data")
with open(
    os.path.join(imo_path, "imo_by_type_SQ" + ".pkl"), "wb") as f:
    pickle.dump(imo_by_type, f)
with open(
    os.path.join(imo_path, "imo_by_type_FS_2030" + ".pkl"), "wb") as f:
    pickle.dump(imo_by_type_2030, f)
with open(
    os.path.join(imo_path, "imo_by_type_FS_2040" + ".pkl"), "wb") as f:
    pickle.dump(imo_by_type_2040, f)
with open(
    os.path.join(imo_path, "imo_by_type_FS_2050" + ".pkl"), "wb") as f:
    pickle.dump(imo_by_type_2050, f)
