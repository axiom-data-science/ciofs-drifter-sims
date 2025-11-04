---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.17.2
kernelspec:
  display_name: ciofs3-report
  language: python
  name: python3
---

```{code-cell} ipython3
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
import holoviews as hv
from bokeh.models import FixedTicker

from myst_nb import glue
import subprocess

ins_type = "drifters"  # instrument name
models = ["CIOFS3"]
years = [1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 
         2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]


model, model_title = "CIOFS3", "CIOFSv3"
depth_cutoff = 7.5

# can only do these when running in docker with playwright available
# once they exist, can run outside of docker because don't need to
# recreate the png files
run_pdf = True
```

```{code-cell} ipython3
:tags: [remove-input]

def save_png(abs_path, figname):
    # if not run_pdf:
    #     print("Skipping PNG creation because run_pdf is False")
    #     return
    # Define the command and its arguments
    cmd = [
        "playwright",
        "screenshot",
        f"file://{abs_path}",
        f"{figname}.png",
        # "--full-page",
        "--wait-for-timeout=30000"
    ]

    # Run the command
    if not Path(f"{figname}.png").exists():
        result = subprocess.run(cmd, capture_output=True, text=True)
```

# Overview of Model Performance for Drifter Data

The performance of the CIOFSv3 model for drifter data is summarized on this page. Shown below are a map of dataset locations and overview maps showing markers colored to indicate the skill score of the model-data comparisons for each dataset. There are two types of skill scores used; see details describing drifter simulations and metrics {ref}`here <page:drifter_description>`.

* [80MB zipfile of plots](https://files.axds.co/ciofs3/zip/drifters.zip)
* [80MB Drifter model-data comparison as PDF](https://files.axds.co/ciofs3/pdfs/drifters.pdf)

```{code-cell} ipython3
:tags: [remove-input, remove-output]

slugs = ["drifters_ecofoci", "drifters_uaf", "drifters_epscor", "drifters_lake_clark"]
slug_names = {
    "drifters_ecofoci": "EcoFOCI",
    "drifters_uaf": "UAF",
    "drifters_epscor": "EPSCoR",
    "drifters_lake_clark": "Lake Clark",
}


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
            
            ds_dataset = cat[dataset_id].read()

            dftemp = pd.read_csv(f'{base_dir}/{dataset_id}_df_interpolated.csv')
            # print(dataset_id, dftemp.cf["Z"], cat[dataset_id].read().cf["Z"])
            dftemp = dftemp.rename(columns={"Unnamed: 0": "time"})
            dftemp["start_lon"] = float(dftemp[dftemp.cf["longitude"].name].iloc[0])
            dftemp["start_lat"] = float(dftemp[dftemp.cf["latitude"].name].iloc[0])
            dftemp["station"] = dataset_id
            # dftemp[["depth_m"]] = dftemp.cf["Z"]
            dftemp[f"{model}_ss1"] = float(ds["ss1"])
            dftemp[f"{model}_ss3_max"] = float(ds["ss3_max"])
            dftemp[f"{model}_ss3_mean"] = float(ds["ss3_mean"])
            dftemp.rename(columns={dftemp.cf["longitude"].name: "longitude", 
                                   dftemp.cf["latitude"].name: "latitude",
                                   }, inplace=True)
                                #    dftemp.cf["Z"].name: "depth_m"}, inplace=True)

            # Create Shapely Point geometries from the DataFrame coordinates
            geometry = dftemp.apply(lambda row: Point(row[dftemp.cf["longitude"].name], row[dftemp.cf["latitude"].name]), axis=1)

            # Create a LineString from the points
            # print(slug, dataset_id)
            # import pdb; pdb.set_trace()
            if len(geometry.tolist()) > 1:
                line = LineString(geometry.tolist())
            else:
                continue
            
            # Create a dictionary for the new row
            rows.append([dftemp["time"].iloc[0], dftemp["time"].iloc[-1], dftemp["start_lon"].iloc[0], dftemp["start_lat"].iloc[0], 
                         f"{float(ds_dataset.cf["Z"].iloc[0])} m", float(ds_dataset.cf["Z"].iloc[0]),
                        #  f"{float(dftemp["depth_m"].iloc[-1])} m", float(dftemp["depth_m"].iloc[-1]),
                        dftemp["station"].iloc[0], dftemp[f"{model}_ss1"].iloc[0], 
                        dftemp[f"{model}_ss3_max"].iloc[0], dftemp[f"{model}_ss3_mean"].iloc[0], line, slug, slug_names[slug]])
            
            dss.append(ds)
            dfs.append(dftemp)

    gdf[model] = gpd.GeoDataFrame(rows, columns=["start_time", "end_time", "start_loc", "end_loc", 
                                                 "depth_m", "depth_val",
                                                 "station", f"{model}_ss1", f"{model}_ss3_max", f"{model}_ss3_mean", "geometry", "slug", "slug_names"])#, geometry=gpd.GeoSeries())

    # dfconcat = pd.concat(dfs)
    # dfconcat = dfconcat.drop(columns=["depth_m"])
    # df[model] = dfconcat
df = pd.concat(dfs)
df["depth_m"] = df["depth_m"].ffill()
# df = df.drop(columns=["depth_m"])
```

```{code-cell} ipython3
:tags: [remove-input]

dfsub = df[["latitude", "longitude", "station"]]
dfsub = dfsub.drop_duplicates(subset="station", keep="last")

cmapss = cmocean.tools.crop_by_percent(cmo.curl, 20, which='both')
```

## Map of Drifters

```{code-cell} ipython3
:tags: [remove-input]

figname = f"build_figures/{ins_type}_map"
abs_path = os.path.abspath(f"{figname}.html")

fmap = gdf["CIOFS3"].hvplot.paths(x="lon", y="lat", geo=True, tiles=True,
                                   #  # xlim=[-153, -150], ylim=[59,60], 
                                    # hover_cols=["label"],#,"date_time","slug"],
                                    # by="slug_names", #clabel=station,
                                    by=["slug_names","depth_m"], #clabel=station,
                                   legend="top_left", line_width=2, coastline=False, 
                                    xlabel="Longitude", ylabel="Latitude", 
                                    title="Drifters", alpha=0.9,
                                    width=600, height=700, fontscale=1.5, )
if not Path(f"{figname}.png").exists():
    hv.save(fmap, figname, fmt='html')
    save_png(abs_path, figname)

glue("fig_map", fmap, display=False)
```



+++

```{figure} build_figures/drifters_map.png
:name: "fig-overview-drifters-map"

All drifter deployments, by project. Click on a legend entry to toggle the transparency.
```

+++

## Results

Results are separated by depth since there is a strong freshwater influence shallower than about 7.5m depth. The model demonstrates skill across both skill score formulations and throughout the water column.

```{code-cell} ipython3
:tags: [remove-input]

plot_kwargs = dict(
      c="ss_code", 
                   hover=False, geo=True, tiles=True, 
                   width=600, height=700, 
                  xlabel="Longitude", ylabel="Latitude", 
                  by=["depth_m"], 
                  # by=["slug_names","depth_m"], 
                  legend="top_left",
                  fontscale=1.5, line_width=1.5, 
                  # title="title".capitalize(), clabel="clabel"
                  )


# setup for changing colorbar from continuous to categorical
# which saves SO MUCH MEMORY
nbins = 11  # -1 to 1 in steps of 0.2
cat_bins = np.linspace(-1, 1, nbins)
ticks = np.linspace(-10, 10, nbins)
tick_labels = {i: f"{i/(nbins-1):.1f}" for i in ticks}

color_kwargs = dict(color_levels=10,
            clim=(-10,10),
            colorbar_opts={'ticker': FixedTicker(ticks=ticks), 
                        'major_label_overrides': tick_labels},
            color="ss_code", 
            cmap=cmapss,
            colorbar=True,
)
```

```{code-cell} ipython3
:tags: [remove-input]

def plot_metric(gdfuse, metric, title, clabel):
    plot_kwargs.update(dict(title=title, clabel=clabel))
    gdfuse["cats"] = pd.cut(gdfuse[metric], cat_bins).to_frame()
    gdfuse["ss_code"] = gdfuse["cats"].cat.codes
    gdfuse["ss_range"] = gdfuse["cats"].astype(str)
    return gdfuse.hvplot.paths(**plot_kwargs).opts(hv.opts.Path(**color_kwargs))
```

```{code-cell} ipython3
:tags: [remove-input]

def choose_title(metric, which_depth_cutoff):
    if "ss1" in metric:
        title = f"Area-Based SS: {which_depth_cutoff}"
    elif "ss3" in metric:
        title = f"Separation Distance, Mean: {which_depth_cutoff}"
    clabel = f"{model_title} {title}"
    return title, clabel

def make_figures(gdf, base_metric):
    metric = f"{model}_{base_metric}"

    # Shallow plot
    which = "shallow"
    gdfuse = gdf[model][gdf[model]["depth_val"] <= depth_cutoff]
    which_depth_cutoff = f"{depth_cutoff}m and {which}er"
    title, clabel = choose_title(metric, which_depth_cutoff)
    plot1 = plot_metric(gdfuse, metric, title, clabel)
    
    # Deep plot
    which = "deep"
    gdfuse = gdf[model][gdf[model]["depth_val"] > depth_cutoff]
    which_depth_cutoff = f"{depth_cutoff}m and {which}er"
    title, clabel = choose_title(metric, which_depth_cutoff)
    plot2 = plot_metric(gdfuse, metric, title, clabel)

    figname = f"build_figures/{ins_type}_{base_metric}"
    abs_path = os.path.abspath(f"{figname}.html")

    variable_plot = plot1 + plot2

    if not Path(f"{figname}.png").exists():
        hv.save(variable_plot, figname, fmt='html')
        if run_pdf:
            save_png(abs_path, figname)

    return variable_plot
```

### Skill Score: Area-Based Length Scale

```{code-cell} ipython3
:tags: [remove-input, remove-output]

base_metric = "ss1"

fig_ss1 = make_figures(gdf, base_metric)
glue("fig_ss1", fig_ss1, display=False)
```



+++

```{figure} build_figures/drifters_ss1.png
:name: "fig-overview-drifters-ss1"

CIOFSv3 area-based skill scores for comparing the model with drifters shallower than (left) and deeper than 7.5m (right), by depth.
```

+++

### Skill Score: Separation Distance, Mean

```{code-cell} ipython3
:tags: [remove-input, remove-output]

base_metric = "ss3_mean"

fig_ss3 = make_figures(gdf, base_metric)
glue("fig_ss3", fig_ss3, display=False)
```



+++

```{figure} build_figures/drifters_ss3_mean.png
:name: "fig-overview-drifters-ss3"

CIOFSv3 separation-distance skill scores (mean) skill scores for comparing the model with drifters shallower than (left) and deeper than 7.5m (right), by depth. Click on a legend entry to toggle the transparency.
```
