# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import plotly as py
import plotly.express as px
import plotly.graph_objects as go
import plotly.offline as offline


df = pd.read_csv(
    "/Users/franziskadettner/Nextcloud/KlimaSchiff"
    "/Data/VESSELFINDER/07JUL2015-5min-vessel-movements-report.csv",
    sep=",",
    index_col=0,
    parse_dates=True,
)

df.head()
data = []
# colors = {df.imo.unique()[0]: "red", df.imo.unique()[1]: "blue"}
df.reset_index(inplace=True)

for i in df.IMO.unique()[0:300]:
    df_imo = df.loc[df.IMO == i]
    df_imo.sort_values(by="DATE TIME (UTC)", inplace=True)
    df_imo.reset_index(drop=True, inplace=True)
    #    if j != len(df_imo)-1:
    data.append(
        go.Scattergeo(
            lat=df_imo["LATITUDE"],
            lon=df_imo["LONGITUDE"],
            mode="markers",
            marker=go.scattergeo.Marker(size=14, color="red"),
        )
    )

layout = go.Layout(
    title="VF_July_test",
    height=1500,
    showlegend=False,
    margin={"l": 20, "r": 20, "t": 20, "b": 20},
    mapbox_style="open-street-map",
    mapbox=go.layout.Mapbox(
        bearing=0,
        center=go.layout.mapbox.Center(lat=56, lon=17),
        pitch=0,
        zoom=5.5,
        style="light",
    ),
)


offline.plot(
    {"data": data, "layout": layout}, filename="plot_VF.html", auto_open=True
)
