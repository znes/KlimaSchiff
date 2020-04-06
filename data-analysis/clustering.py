import os

import pandas as pd
from sklearn.cluster import AgglomerativeClustering
import matplotlib.pyplot as plt

path = "/home/admin/nextcloud-znes/KlimaSchiff/Data/Ship_DB"

df = pd.read_excel(
    os.path.join(path, "Ship-DB-TabD-200220.xlsx"),
    sheet_name="Ship-DB-TabD-200220",
)


select = ["Baujahr", "BRT"]

df = df[select].dropna(how="any")

data = df.loc[0:5000, select].values


# cluster data
cluster = AgglomerativeClustering(
    n_clusters=20, affinity="euclidean", linkage="ward"
)
result = cluster.fit_predict(data)


plt.figure(figsize=(10, 7))
plt.scatter(data[:, 0], data[:, 1], c=cluster.labels_, cmap="rainbow")
