import os

import pandas as pd
from sklearn.cluster import AgglomerativeClustering
import matplotlib.pyplot as plt

import seaborn as sns

path = "/home/admin/nextcloud-znes/KlimaSchiff/Data/Ship_DB"

df = pd.read_csv(
    os.path.join(path, "schiffsdatenbank.csv"), index_col=0
)

mapper = pd.read_csv(
    os.path.join(path, "schiffstypen_FSG.csv"), index_col=0
)

# create dict mapper ship types
dict_mapper = {
    row["Unnamed: 1"]: row["Zuordnung Rolf"].replace(" ", "_").replace("/", "-")
    for (idx, row) in mapper.iterrows()
}

# map types
df["type"] = df["Schiffstyp"].apply(lambda x: dict_mapper[x])

for stype in df["type"].unique():
    sub_df = df.loc[(df["type"] == stype)]
    # remove top 10 indices in both dimensions
    head2 = sub_df.sort_values(by=['Laenge'], ascending=[False]).head(10)
    head1 = sub_df.sort_values(by=['BRZ'], ascending=[False]).head(10)
    sub_df.drop(head1.index.append(head2.index), inplace=True)

    ax = sns.jointplot(
        x=sub_df["Laenge"][::10],
        y=sub_df["BRZ"][::10],
        marginal_kws=dict(bins=200, rug=True),
        kind='scatter', color="darkblue", edgecolor="skyblue")
    ax.set_axis_labels("BRZ", "Length")

    plt.savefig(
        os.path.join(path,"jointplot-{}.pdf".format(stype)),
        #bbox_extra_artists=(),
        figsize=(15, 8),
        bbox_inches="tight",
    )


# 
# select = ["Laenge", "BRZ", "Breite"]
# df = df[select].dropna(how="any")
# data = sub_df.loc[0:2000, select].values
# # cluster data
# cluster = AgglomerativeClustering(
#     n_clusters=10, affinity="euclidean", linkage="ward"
# )
# result = cluster.fit_predict(data)
# ax = plt.scatter(data[:, 0], data[:, 1], data[:, 2], c=cluster.labels_, cmap="rainbow")
# plt.savefig(
#     os.path.join(path,"cluster-{}.pdf".format(stype)),
#     #bbox_extra_artists=(),
#     figsize=(15, 8),
#     bbox_inches="tight",
# )
#
#
# from mpl_toolkits.mplot3d import Axes3D
#
# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# # plotting 3D trisurface plot
# ax.scatter(df["Laenge"], df["Breite"], df["BRZ"],
#                 cmap = "Accent", linewidth = 0.2)
