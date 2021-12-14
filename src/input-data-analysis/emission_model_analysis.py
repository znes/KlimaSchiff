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
sns.set_style('darkgrid')
for shiptype in shiptypes:
    pollutant = "CO2 [kg]"
    engine = "Propulsion"
    #shiptype = "Tanker SuezMax"
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
        ax=ax
    )
    sns.lineplot(
        data=df.loc[idx[shiptype + " Tier I", engine]].reset_index(),
        x="Speed [m/second]",
        y=pollutant,
        label="Tier I",
        ax=ax
    )
    ax.grid()
    ax.set_xlim(0, 13)
    ax.legend()
    plt.savefig("figures/{}-model-{}.pdf".format(pollutant, shiptype))
