import os
import json
from pathlib import PurePath

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

with open("config.json") as file:
    config = json.load(file)
model_data_path = PurePath(os.path.expanduser("~"), config["model_data"])
df = pd.read_csv(
    PurePath(model_data_path, "model_2015_sq.csv"), sep=";", index_col=[0, 1]
)
idx = pd.IndexSlice

shiptypes = set(
    [
        " ".join(i.split(" ")[0:-2])
        for i in df.index.get_level_values(0).unique()
        if not "FS" in i
    ]
)

pollutants = df.columns[8:13].drop("CH4 [kg]")
#pollutants = ["Energy [J]", "NMVOC [kg]"]
sns.set_style("darkgrid")
for shiptype in shiptypes:
    for pollutant in pollutants:
        # if "Ro-Pax" in shiptype:
        #pollutant = "Energy [J]"
        engine = "Propulsion"
        # shiptype = "Tanker SuezMax"
        plt.figure()
        ax = sns.lineplot(
            data=df.loc[idx[shiptype + " FS", engine]].reset_index(),
            x="Speed [m/second]",
            y=pollutant,
            label="FS",
        )
        # ax = [pollutant].plot(label="FS")
        sns.lineplot(
            data=df.loc[idx[shiptype + " Tier II", engine]].reset_index(),
            x="Speed [m/second]",
            y=pollutant,
            label="Tier II",
            ax=ax,
        )
        ax = sns.lineplot(
            data=df.loc[idx[shiptype + " FS", "Electrical"]].reset_index(),
            x="Speed [m/second]",
            y=pollutant,
            label="Aux-FS",
        )
        # ax = [pollutant].plot(label="FS")
        sns.lineplot(
            data=df.loc[
                idx[shiptype + " Tier II", "Electrical"]
            ].reset_index(),
            x="Speed [m/second]",
            y=pollutant,
            label="Aux-Tier II",
            ax=ax,
        )
        # sns.lineplot(
        #     data=df.loc[idx[shiptype + " Tier I", engine]].reset_index(),
        #     x="Speed [m/second]",
        #     y=pollutant,
        #     label="Tier I",
        #     ax=ax
        # )
        ax.grid()
        ax.set_xlim(0, 13)
        ax.set_title(shiptype)
        ax.legend()
        plt.savefig("figures/{}-model-{}.pdf".format(pollutant, shiptype))
