import pandas as pd
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns


with open("config.json") as file:
    config = json.load(file)

df = pd.read_csv(
    os.path.join(
        os.path.expanduser("~"),
        config["result_data"],
        "total_emissions_by_type_and_day.csv",
    ),
    parse_dates=True,
)

# df_m = df.unstack(level=1).resample("M").sum().unstack().unstack(level=0).swaplevel(0,1)

categories = [
    "Tanker",
    "Bulker",
    "Container",
    "Cruise",
    "Cargo",
    "Ro-Ro",
    "Ro-Pax",
    "MPV",
    "Car Carrier",
    "Diverse",
]


def category(row):
    check = [cat for cat in categories if cat in row]
    if check:
        return check[0]


df["category"] = df["Unnamed: 1"].apply(lambda x: category(x))

df["Unnamed: 0"] = pd.to_datetime(df["Unnamed: 0"], format="%Y%m%d")
# remove 2014 data from results data set
df = df.set_index("Unnamed: 0")["2015"].reset_index()
# df.set_index(["Unnamed: 0","Unnamed: 1"], inplace=True)
df_sums = df.groupby(["Unnamed: 0", "category"]).sum()

# df_comp = df[[c for c in df.columns if "CO2" in c]].sum()
pollutants = set(
    ["SOx", "NOx", "PM", "CO [kg]", "CO2", "ASH", "POA", "NMVOC", "BC"]
)

def correct_categories(cols):
    return [cat for col in cols for cat in pollutants if cat in col]


df_sums = df_sums.T
df_sums["component"] = correct_categories(df_sums.index)
df_time = df_sums.reset_index().groupby("component").sum().T


# for shipclass in df_time.index.get_level_values(1).unique():
for pollutant in df_time.columns:
    data = df_time.loc[:, pollutant]
    data = data.unstack()
    positions = [
        p
        for p in data.index
        if p.hour == 0 and p.is_month_start and p.month in range(1, 13, 1)
    ]
    labels = [l.strftime("%m-%d") for l in positions]
    ax = data.plot(grid=True)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Emissions per day in kg")
    ax.set_xlim(positions[0], positions[-1])
    ax.set_xlabel("Day")
    lgd = ax.legend(title="Type", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.set_title("{}-Emissions in SQ-scenario".format(pollutant))
    plt.savefig(
        "figures/results/Daily_{}_emissions_SQ.pdf".format(pollutant),
        bbox_extra_artists=(lgd,),
        bbox_inches="tight",
    )


# aggregated numbers yearly --------------------------------------------
df_time_agg = df_time.reset_index().groupby("category").sum()
df_time_agg.to_csv("tables/yearly_emissions_by_shiptype_and_pollutant_SQ.csv")

plot_data = (
    df_time_agg.drop(["CO2", "NOx", "CO [kg]", "SOx"], axis=1)
    .stack()
    .reset_index()
)
sns.barplot(x="component", y=0, hue="category", data=plot_data)
#

ax = df_time_agg[["NOx", "CO [kg]", "SOx"]].divide(1e9).plot(kind="bar")
ax.set_ylabel("CO2 in Mio ton")
ax.set_xlabel("Ship type")
plt.savefig("figures/results/Agg_CO2_emissions_SQ.pdf")

# -----------------------------------------------------------------------------
# scenario comparison
# ---------------------------------------------------------------------------
scenarios = ["2015_sq", "2030_low", "2030_high", "2040_low"]
pollutants = [
    i + " [kg]" for i in ["SOx", "NOx", "PM", "CO", "CO2", "ASH", "POA", "NMVOC", "BC"]]

d = {}
with open("config.json") as file:
    config = json.load(file)
config["intermediate_data"] = "nextcloud-znes/KlimaSchiff/result_data/emissions"
for scenario in scenarios:
    scenario_path = os.path.join(
        os.path.expanduser("~"),
        config["intermediate_data"],
        scenario,
    )

    df = pd.read_csv(os.path.join(scenario_path, "total_emissions_by_type_and_day.csv"))

    # group by category ("Bulker", "Tanker" etc)
    df["Shipclass"] = df["Unnamed: 1"].apply(lambda x: category(x))

    df["Unnamed: 0"] = pd.to_datetime(df["Unnamed: 0"], format="%Y%m%d")
    # remove 2014 data from results data set
    df = df.set_index("Unnamed: 0")["2015"].reset_index()
    # df.set_index(["Unnamed: 0","Unnamed: 1"], inplace=True)
    df_sums = df.groupby(["Unnamed: 0", "Shipclass"]).sum()
    df_sums = df_sums.sum(level=1, axis=0).T

    df_sums["Pollutant"] = [row.split("-")[1] for row in df_sums.index]

    d[scenario] = df_sums #.groupby("Pollutant").sum()


pd.DataFrame({k:v.sum(axis=1) for k,v in d.items()}).to_csv(
    "tables/annual_emissions_all_scenarios_by_engine.csv")
pd.DataFrame({k:v.groupby("Pollutant").sum().sum(axis=1) for k,v in d.items()}).to_csv(
    "tables/annual_emissions_all_scenarios_total.csv")

heatmap = {}
for scenario in d:
    d[scenario].to_csv("tables/annual_emission_by_type_{}.csv".format(scenario))
    ref = d["2015_sq"].groupby("Pollutant").sum().loc[pollutants]
    hm = d[scenario].groupby("Pollutant").sum().loc[pollutants].div(ref.values).sub(1)
    hm.index = [i.replace(" [kg]", "") for i in hm.index]
    #hm = hm.round(2)
    heatmap[scenario] = hm
    fig, ax = plt.subplots(figsize=(10,6))

    sns.heatmap(heatmap[scenario], cmap="YlGnBu_r", cbar_kws={'label': 'Deviation to SQ'},
          annot=True, ax=ax, fmt=".2%")
    plt.savefig(
        "figures/results/heatmap_emission_reduction_{}.pdf".format(scenario),
        bbox_inches="tight",)
