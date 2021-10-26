import pandas as pd
import os
import json

with open("config.json") as file:
    config = json.load(file)

df = pd.read_csv(
    os.path.join(
        os.path.expanduser("~"),
        config["result_data"],
    "total_emissions_by_type_and_day.csv"),  parse_dates=True
    )

#df_m = df.unstack(level=1).resample("M").sum().unstack().unstack(level=0).swaplevel(0,1)

categories = [
    "Tanker", "Bulker", "Container",
    "Cruise", "Car", "Ro-Ro", "Ro-Pax",
    "MPV", "Car Carrier", "Diverse"]
def category(row):
    check = [cat for cat in categories if cat in row]
    if check:
        return check[0]
df["category"] = df["Unnamed: 1"].apply(lambda x: category(x))

df["Unnamed: 0"] = pd.to_datetime(df["Unnamed: 0"], format="%Y%m%d")
# remove 2014 data from results data set
df = df.set_index("Unnamed: 0")["2015"].reset_index()
#df.set_index(["Unnamed: 0","Unnamed: 1"], inplace=True)
df_sums = df.groupby(["Unnamed: 0", "category"]).sum()
#df_comp = df[[c for c in df.columns if "CO2" in c]].sum()
categories = set(["SOx", "NOx", "PM", "CO [kg]", "CO2", "ASH", "POA", "NMVOC", "BC"])
def correct_categories(cols):
    return [cat for col in cols for cat in categories if cat in col]
df_sums = df_sums.T
df_sums["component"] = correct_categories(df_sums.index)


df_time = df_sums.reset_index().groupby("component").sum().T
df_time_agg = df_time.reset_index().groupby("category").sum()

ax = df_time_agg["CO2"].divide(1e9).plot(kind="bar")
ax.set_ylabel("CO2 in Mio ton")
