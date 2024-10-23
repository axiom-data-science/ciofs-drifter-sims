---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.4
kernelspec:
  display_name: ciofs-drifter-sims
  language: python
  name: python3
---

```{code-cell}
:tags: [remove-input]

import pandas as pd
import cf_pandas
import cook_inlet_catalogs as cic
import intake
# import ciofs_drifter_sims
from importlib.resources import files
import os
import hvplot.pandas
import numpy as np
import xarray as xr
from shapely.geometry import Point, LineString
import geopandas as gpd
import cmocean.cm as cmo
import cmocean.tools
import geoviews as gv
import geoviews.feature as gf
from pathlib import Path

from myst_nb import glue
```

# Overview of Model Performance for Drifter Data

See details describing drifter simulations and metrics {ref}`here <page:drifter_description>`.

[100MB zipfile of plots](https://files.axds.co/ciofs_fresh/zip/drifters.zip)

```{code-cell}
:tags: [remove-input]

slugs = ["drifters_ecofoci", "drifters_uaf"]

models = ["CIOFS", "CIOFSFRESH"]

# dftemptemps = {}
dfs = []
dss = []
rows = []
gdf = {}
df = {}
for model in models:

    # base_dir = files(ciofs_drifter_sims) / model
    base_dir = Path("..") / model

    for slug in slugs:
        cat = intake.open_catalog(cic.utils.cat_path(slug))
        dataset_ids = list(cat)
        for dataset_id in dataset_ids:
            if not os.path.exists(f"{base_dir}/{dataset_id}.png") and not os.path.exists(f"{base_dir}/{dataset_id}_ds_ss.nc"):
                # print(f"Skipping {dataset_id}")
                continue
            # else:
            #     print(f"Processing {dataset_id}")
            ds = xr.open_dataset(f"{base_dir}/{dataset_id}_ds_ss.nc")

            dftemp = pd.read_csv(f'{base_dir}/{dataset_id}_df_interpolated.csv')
            dftemp = dftemp.rename(columns={"Unnamed: 0": "time"})
            dftemp["start_lon"] = float(dftemp[dftemp.cf["longitude"].name].iloc[0])
            dftemp["start_lat"] = float(dftemp[dftemp.cf["latitude"].name].iloc[0])
            dftemp["station"] = dataset_id
            dftemp[f"{model}_ss1"] = float(ds["ss1"])
            dftemp[f"{model}_ss3_max"] = float(ds["ss3_max"])
            dftemp[f"{model}_ss3_mean"] = float(ds["ss3_mean"])
            dftemp.rename(columns={dftemp.cf["longitude"].name: "longitude", dftemp.cf["latitude"].name: "latitude"}, inplace=True)

            # Create Shapely Point geometries from the DataFrame coordinates
            geometry = dftemp.apply(lambda row: Point(row[dftemp.cf["longitude"].name], row[dftemp.cf["latitude"].name]), axis=1)

            # Create a LineString from the points
            line = LineString(geometry.tolist())
            
            # Create a dictionary for the new row
            rows.append([dftemp["time"].iloc[0], dftemp["time"].iloc[-1], dftemp["start_lon"].iloc[0], dftemp["start_lat"].iloc[0],
                        dftemp["station"].iloc[0], dftemp[f"{model}_ss1"].iloc[0], 
                        dftemp[f"{model}_ss3_max"].iloc[0], dftemp[f"{model}_ss3_mean"].iloc[0], line])
            
            dss.append(ds)
            dfs.append(dftemp)

    gdf[model] = gpd.GeoDataFrame(rows, columns=["start_time", "end_time", "start_loc", "end_loc", "station", f"{model}_ss1", f"{model}_ss3_max", f"{model}_ss3_mean", "geometry"])#, geometry=gpd.GeoSeries())

    # dfconcat = pd.concat(dfs)
    # dfconcat = dfconcat.drop(columns=["depth_m"])
    # df[model] = dfconcat
df = pd.concat(dfs)
df["depth_m"] = df["depth_m"].ffill()
# df = df.drop(columns=["depth_m"])
```

```{code-cell}
:tags: [remove-input]

dfsub = df[["latitude", "longitude", "station"]]
dfsub = dfsub.drop_duplicates(subset="station", keep="last")

cmapss = cmocean.tools.crop_by_percent(cmo.curl, 20, which='both')
```

```{code-cell}
:tags: [remove-input]

def line_plot_times_pts_plot(gdf, df, line_kwargs, pts_kwargs):
    # This plot is what I want, but due to a bug it can't have hover and color by column
    # https://github.com/holoviz/hvplot/issues/792
    # import pdb; pdb.set_trace()
    line_plot = gv.Path(gdf).opts(**line_kwargs)

    # So use the following plot of points to provide the hover feature.
    # has the added benefit of provided time dimension along the track.
    p = cic.utils.points_dict(**pts_kwargs)
    p.pop("color")
    p.update(dict(coastline="10m", fontscale=1.5))

    # decimate the points some to save memory since this is just for hover
    pts_plot = df[::4].hvplot(**p)

    return line_plot * pts_plot
```

## Map of Drifters

```{code-cell}
:tags: [remove-input]

line_kwargs = dict(line_width=1.5, width=600, height=700, color="station", cmap=cmo.phase)
pts_kwargs = dict(x=df.cf["longitude"].name, y=df.cf["latitude"].name, hover_cols=["depth_m"],
                          size=1, title="Drifters", tiles=True, c="station", cmap=cmo.phase)

model = "CIOFS"
plot1 = line_plot_times_pts_plot(gdf[model], df, line_kwargs, pts_kwargs)
model = "CIOFSFRESH"
plot2 = line_plot_times_pts_plot(gdf[model], df, line_kwargs, pts_kwargs)


# # have one point labeled
# labels_plot = dfsub.hvplot.labels(x=df.cf["longitude"].name, y=df.cf["latitude"].name, text="station", geo=True, 
#                                text_alpha=0.5, text_color="k",
#                                hover=False, text_baseline='bottom', fontscale=1.5, text_font_size='10pt')

fmap = plot1 * plot2

# gv.tile_sources.OSM * plot1 * plot2 #* labels_plot
glue("fig_map", fmap, display=False)
```

```{glue:figure} fig_map
:name: "fig-overview-drifters-map"

All drifter deployments.
```

+++

## Results

+++

### Skill Score: Area-Based Length Scale

```{code-cell}
:tags: [remove-input, full-width]

basemetric, clabel = "ss1", "Skill Score: Area-Based Length Scale"

model, model_title = "CIOFS", "CIOFS Hindcast"
metric = f"{model}_{basemetric}"
line_kwargs = dict(line_width=1.5, width=600, height=700, color=metric, 
                   cmap=cmapss, clim=(-1, 1), colorbar=True)
pts_kwargs = dict(x=df.cf["longitude"].name, y=df.cf["latitude"].name,
                          c=metric, hover_cols=["station", "time", "depth_m", metric], size=1, title=model_title, cmap=cmapss,
                          clabel=clabel, clim=(-1, 1))
left = line_plot_times_pts_plot(gdf[model], df.dropna(subset=metric), line_kwargs, pts_kwargs)

model, model_title = "CIOFSFRESH", "CIOFS Freshwater"
metric = f"{model}_{basemetric}"
line_kwargs = dict(line_width=1.5, width=600, height=700, color=metric, 
                   cmap=cmapss, clim=(-1, 1), colorbar=True)
pts_kwargs = dict(x=df.cf["longitude"].name, y=df.cf["latitude"].name,
                          c=metric, hover_cols=["station", "time", "depth_m", metric], size=1, title=model_title, cmap=cmapss,
                          clabel=clabel, clim=(-1, 1))
right = line_plot_times_pts_plot(gdf[model], df.dropna(subset=metric), line_kwargs, pts_kwargs)

plot = left + right
glue("ss1", plot, display=False)
```

````{div} full-width   
```{glue:figure} ss1
:name: "fig-overview-drifters-ss1"

Area-based skill scores for CIOFS Hindcast (left) and CIOFS Freshwater (right) with drifters.
```
````

+++

### Skill Score: Separation Distance, Mean

```{code-cell}
:tags: [remove-input, full-width]

basemetric, clabel = "ss3_mean", "Skill Score: Separation Distance, Mean"

model, model_title = "CIOFS", "CIOFS Hindcast"
metric = f"{model}_{basemetric}"
line_kwargs = dict(line_width=1.5, width=600, height=700, color=metric, 
                   cmap=cmapss, clim=(-1, 1), colorbar=True)
pts_kwargs = dict(x=df.cf["longitude"].name, y=df.cf["latitude"].name,
                          c=metric, hover_cols=["station", "time", "depth_m", metric], size=1, title=model_title, cmap=cmapss,
                          clabel=clabel, clim=(-1, 1))
left = line_plot_times_pts_plot(gdf[model], df.dropna(subset=metric), line_kwargs, pts_kwargs)

model, model_title = "CIOFSFRESH", "CIOFS Freshwater"
metric = f"{model}_{basemetric}"
line_kwargs = dict(line_width=1.5, width=600, height=700, color=metric, 
                   cmap=cmapss, clim=(-1, 1), colorbar=True)
pts_kwargs = dict(x=df.cf["longitude"].name, y=df.cf["latitude"].name,
                          c=metric, hover_cols=["station", "time", "depth_m", metric], size=1, title=model_title, cmap=cmapss,
                          clabel=clabel, clim=(-1, 1))
right = line_plot_times_pts_plot(gdf[model], df.dropna(subset=metric), line_kwargs, pts_kwargs)

plot = left + right
glue("ss3", plot, display=False)
```

````{div} full-width   
```{glue:figure} ss3
:name: "fig-overview-drifters-ss3"

Separation-distance skill scores for CIOFS Hindcast (left) and CIOFS Freshwater (right) with drifters.
```
````
