"""Main script"""

import os
import cf_xarray
import cf_pandas
import intake
import particle_tracking_manager as ptm
import particle_tracking_manager.plotting
import pandas as pd
import cmocean.cm as cmo
import cartopy.crs as ccrs
import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import alphashape
import yaml
from shapely import wkt
from utils import add_drifter_track_to_plot, add_feature_to_plot, calc_distance_drifter_qhull, calc_qhull, calc_ss, plot_ss_qhull, plot_ss_sep
from cartopy.feature import ShapelyFeature
from shapely.geometry import Polygon, Point, LineString

# years = [2002, 2003, 2004]  # v4a DONE
# years = [2011, 2012]  # v4b DONE
# years = [2021, 2022, 2023]  # v4c DONE  
# years = [1999, 2000, 2001]  # v4d DONE RERUN
# years = [2006, 2007, 2008]  # v4e DONE
# years = [2009, 2010]  # v4f DONE
# years = [2014, 2015, 2016]  # v4g DONE
# years = [2017, 2018]  # v4h DONE
# years = [2019, 2020]  # v4i DONE
# years = [2005, 2013, 2024]  # v4j 
# years = [1999, 2000, 2001, 2002, 2003, 2004, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 
#          2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]  # v4



years = [1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 
         2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]



# years = [1999]  # DONE ECOFOCI, DONE UAF
# years = [2000]  # DONE ECOFOCI, DONE UAF
# years = [2001]  # DONE ECOFOCI, DONE UAF
# years = [2002]  # DONE ECOFOCI, DONE UAF
# years = [2003]  # DONE ECOFOCI, DONE UAF
# years = [2004]  # DONE ECOFOCI, DONE UAF
# years = [2005]  # DONE ECOFOCI, DONE UAF
# years = [2006]  # DONE ECOFOCI, DONE UAF

# years = [2007]  # DONE ECOFOCI, DONE UAF
# years = [2008]  # DONE ECOFOCI, DONE UAF
# years = [2009]  # DONE ECOFOCI, DONE UAF
# years = [2010]  # DONE ECOFOCI, DONE UAF
# years = [2011]  # DONE ECOFOCI, DONE UAF
# years = [2012]  # DONE ECOFOCI, DONE UAF
# years = [2013]  # DONE ECOFOCI, DONE UAF
# years = [2014]  # DONE ECOFOCI, DONE UAF

# years = [2015]  # DONE ECOFOCI, DONE UAF
# years = [2016]  # DONE ECOFOCI, DONE UAF
# years = [2017]  # DONE ECOFOCI, DONE UAF
# years = [2018]  # DONE ECOFOCI, DONE UAF
# years = [2019]  # DONE ECOFOCI, DONE UAF
# years = [2020]  # DONE ECOFOCI, DONE UAF
# years = [2021]  # DONE ECOFOCI, DONE UAF
# years = [2022]  # DONE ECOFOCI, DONE UAF

# years = [2023]  # DONE ECOFOCI, DDNE UAF
# years = [2024]  # DONE ECOFOCI, DONE UAF



# cat_models = intake.open_catalog("models.yaml")
# models = ["CIOFSFRESH"]
models = ["CIOFS3"]
# years left: 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015
# 57887_y2005 spans 2005 and 2006
# run by ranges instead
# dids = 5
# icount = 0  # DONE 
# icount = 1  # DONE 
# icount = 2  # DONE
# icount = 3  # DONE
# icount = 4  # DONE
# icount = 5  # DONE
# icount = 6  # DONE
# icount = 7  # DONE
# icount = 74  # DONE
# icount = 75  # DONE
# icount = 76  # DONE
# icount = 77  # DONE
# icount = 78  # DONE

# drifter_slugs = ["drifters_ecofoci"]  


# dids = 19
# # icount = 4  # running (2)
# # icount = 5  # DONE (3)
# # icount = 6  # DONE (4)
# icount = 7  # DONE (5)

dids = 5
icount = 18  
# icount = 19  # DONE
# icount = 20  # DONE
# icount = 21  # DONE
# icount = 22  # DONE
# icount = 23  # DONE
# icount = 24  # DONE

drifter_slugs = ["drifters_uaf"]  # 154
# drifter_slugs = ["drifters_epscor", "drifters_lake_clark"]

# drifter_slugs = ["drifters_ecofoci"]
# drifter_slugs = ["drifters_uaf", "drifters_epscor", "drifters_lake_clark"]

# models = ["CIOFS"]
# drifter_slugs = ["drifters_epscor"]
# drifter_slugs = ["drifters_lake_clark"]
# drifter_slugs = ["drifters_uaf", "drifters_epscor"]
# drifter_slugs = ["drifters_lake_clark"]
# drifter_slugs = ["drifters_uaf"]
# drifter_slugs = ["drifters_uaf", "drifters_epscor", "drifters_lake_clark"]
# drifter_slugs = ["drifters_epscor", "drifters_lake_clark"]
# drifter_slugs = ["drifters_ecofoci", "drifters_uaf"]#, "drifters_epscor", "drifters_lake_clark"]

slug_names = {"drifters_ecofoci": "EcoFOCI", "drifters_uaf": "UAF", 
              "drifters_epscor": "EPSCoR", "drifters_lake_clark": "Lake Clark"}

col_max = "#8e44ad"
col_mean = "#63ad44"
col_other = "#ff5733"

# # calculate model min/max lon/lat box (same for both CIOFS models)
# m = ptm.OpenDriftModel(ocean_model="CIOFS", 
#                         start_time="2005-2-1", steps=1,
#                         ocean_model_local=True, do3D=False,
#                         number=1, use_static_masks=True)
# m.add_reader()
# lonmin, lonmax = m.reader_metadata("lon").min(), m.reader_metadata("lon").max()
# latmin, latmax = m.reader_metadata("lat").min(), m.reader_metadata("lat").max()
# print(float(lonmin), float(lonmax), float(latmin), float(latmax))
# lonmin, lonmax, latmin, latmax = -156.485291, -148.925125, 56.7004919, 61.5247774

# Instead of the actual limits, use limits that account for the fact that the drifters
# are outside the Inlet
lonmin, lonmax, latmin, latmax = -154.5, -151, 57.5, 61.5

axis = 57.29577951308232  # something to do with pi
globe = ccrs.Globe(ellipse=None,
                    semimajor_axis=axis,
                    semiminor_axis=axis)
crs = ccrs.Mercator(globe=globe)
globe = crs.globe

# # calculate model domain boundary to plot (code from model_catalogs)
# dd, alpha = [1,5]  # dd, alpha, from mc-goods catalog for CIOFS
# loc = "/mnt/vault/ciofs/HINDCAST/ciofs_kerchunk.parq"
# ds =  xr.open_dataset(loc, engine="kerchunk", chunks={})

# lonkey, latkey, maskkey = "lon_rho", "lat_rho", "mask_rho"
# lon = ds[lonkey].where(ds[maskkey] == 1).values
# lon = lon[~np.isnan(lon)].flatten()
# lat = ds[latkey].where(ds[maskkey] == 1).values
# lat = lat[~np.isnan(lat)].flatten()

# lon, lat = lon[::dd], lat[::dd]
# pts = list(zip(lon, lat))

# # low res, same as convex hull
# # p0 = alphashape.alphashape(pts, 0.0)
# p1 = alphashape.alphashape(pts, alpha)
# boundary = p1.wkt
# with open("ciofs_boundary.yaml", "w") as outfile:
#     yaml.dump({"wkt": boundary}, outfile, default_flow_style=False)
# Load the WKT boundary from the YAML file
with open("ciofs_boundary.yaml", "r") as infile:
    data = yaml.safe_load(infile)
    boundary_wkt = data["wkt"]

# Parse the WKT string into a Shapely geometry
boundary_geom = wkt.loads(boundary_wkt)


for model in models:
    print(model)
    basedir = str(model)
    for drifter_slug in drifter_slugs:
        cat_name = f"~/projects/cook-inlet-catalogs/cook_inlet_catalogs/catalogs/{drifter_slug}.yaml"
        cat_drifters = intake.open_catalog(cat_name)
        dataset_ids = list(cat_drifters)
        # dataset_ids = [dataset_id for dataset_id in list(cat_drifters) if years[0] in dataset_id]
        dataset_ids = dataset_ids[(icount)*dids:(icount+1)*dids]

        for dataset_id in dataset_ids:
            print(f"\nChecking {dataset_id}\n")
            
            filename = dataset_id

            # if os.path.exists(f"{basedir}/{filename}.nc"):
            if os.path.exists(f"{basedir}/{filename}.nc") and os.path.exists(f"{basedir}/{filename}_ss_qhull.pdf") and os.path.exists(f"{basedir}/{filename}_ss_sep.pdf") and os.path.exists(f"{basedir}/{filename}.png"):
                print(f"\n{filename} already exists\n")
                continue

            
            print(f"\nChecking {dataset_id}\n")
            df = cat_drifters[dataset_id].read()
            # import pdb; pdb.set_trace()
            
            if isinstance(df, xr.Dataset):
                yearmin, yearmax = df.cf["T"].min().year, df.cf["T"].max().year
            elif isinstance(df, pd.DataFrame):
                yearmin, yearmax = pd.Timestamp(df.cf["T"].iloc[0]).year, pd.Timestamp(df.cf["T"].iloc[-1]).year

            if yearmin not in years or yearmax not in years:
                print(f"\nDrifter {dataset_id} is not in the correct year range; year is {yearmin}\n")
                continue
            
            # compare if the drifter is even in the domain box
            if not df.cf["longitude"].between(lonmin, lonmax).any() or not df.cf["latitude"].between(latmin, latmax).any():
                print(f"\nDrifter {dataset_id} is never in the Cook Inlet domain\n")
                continue

            # otherwise the drifter must sometime be within that box, though it might not actually be within the model domain
            # What is the first time the drifter enters the domain box?

            # don't need tidal flats if drifter is deeper than tidal flats
            # if float(df.cf["Z"][0]) > 5:
            #     use_static_masks = True
            # else:
            #     use_static_masks = False
            use_static_masks = False
            
            print(f"Drifter depth is {float(df.cf['Z'][0])} m")
            # import pdb; pdb.set_trace()
                
            # Drifters didn't start in Cook Inlet! In fact they may never enter the domain. but if they do
            # it might just happen sometime. So we need to find the first time the drifter enters the CIOFS
            # domain during their drift and start the PTM simulation at that time. 
            istart = (df.cf["longitude"].between(lonmin, lonmax) & df.cf["latitude"].between(latmin, latmax)).idxmax()
            # istart returns 0 if all are False so need to check for if istart is 0 for that reason or if
            # the drifter is actually starting in the domain
            if istart == 0 and not df.cf["longitude"].between(lonmin, lonmax).iloc[0] or not df.cf["latitude"].between(latmin, latmax).iloc[0]:
                continue 
            # iend = (df.cf["longitude"].between(lonmin, lonmax) & df.cf["latitude"].between(latmin, latmax)).nonzero()[0][-1]
            endtemp = (df.cf["longitude"].between(lonmin, lonmax) & df.cf["latitude"].between(latmin, latmax)).to_numpy().nonzero()[0]
            if len(endtemp) > 0:
                iend = endtemp[-1]
            else:
                iend = len(df.cf["longitude"]) - 1

            # run PTM simulation
            lon, lat = df.cf["longitude"].iloc[istart], df.cf["latitude"].iloc[istart]
            start_time = pd.Timestamp(df.cf["T"].iloc[istart]) - pd.Timedelta("40T")
            end_time = pd.Timestamp(df.cf["T"].iloc[iend])
            print(lon, lat, start_time)
            # import pdb; pdb.set_trace()
            if os.path.exists(f"{basedir}/{filename}.nc"):
                import opendrift as od
                o = od.open(f"{basedir}/{filename}.nc")
            else:

                m = ptm.OpenDriftModel(ocean_model=model, z=-float(df.cf["Z"][0]),
                                    lon=lon, lat=lat, 
                                    start_time=start_time, end_time=end_time,
                                    start_time_end=pd.Timestamp(df.cf["T"].iloc[istart]),
                                    #    start_time=df.cf["T"][0], end_time=df.cf["T"][0]+pd.Timedelta("2H"),#df.cf["T"].iloc[-1],
                                    # #    start_time_end=df.cf["T"][0]+pd.Timedelta("40T"),
                                    ocean_model_local=False, # for CIOFS3
                                    do3D=False,
                                    radius=500, number=1000, use_static_masks=use_static_masks,
                                    output_file=f"{basedir}/{filename}.nc",
                                    max_speed=50,
                                    coastline_action="previous",
                                    seafloor_action="previous",
                                    # log_level="DEBUG",
                                    save_interpolator=True,
                                    interpolator_filename="CIOFS3_interpolator",
                                    )
                m.run_all()
                o = m.o
            
            # Calculate drifter ss metric
            # if not os.path.exists(f"{filename}_ss.png") and not os.path.exists(f"{filename}B_ss.png"):
            # model_times, ss, sums, ss2, dists, df_interpolated, \
            #     dist_simulated_to_in_situ, dist_along_df_interpolated, separation_distance, ss3 = calc_ss(df, o)
            
            
            if not os.path.exists(f"{basedir}/{filename}_ds_ss.nc") and not os.path.exists(f"{basedir}/{filename}_df_interpolated.csv"):
                ds, df_interpolated = calc_ss(df, o)
                df_interpolated.to_csv(f"{basedir}/{filename}_df_interpolated.csv")
                ds.to_netcdf(f"{basedir}/{filename}_ds_ss.nc")
            else:
                ds = xr.open_dataset(f"{basedir}/{filename}_ds_ss.nc")
                df_interpolated = pd.read_csv(f"{basedir}/{filename}_df_interpolated.csv", parse_dates=True, index_col=0)
            # # ds, df_interpolated = calc_ss(df, o)
            # # import pdb; pdb.set_trace()
            # # plot_ss_qhull(ds, filename)
            # # plot_ss_sep(ds, filename)

            # # # ds, df_interpolated = calc_ss(df, o)
            if not os.path.exists(f"{basedir}/{filename}_ss_qhull.png") and not os.path.exists(f"{basedir}/{filename}_ss_sep.png"):
                plot_ss_qhull(ds, f"{basedir}/{filename}")
                plot_ss_sep(ds, f"{basedir}/{filename}")
                
                
                
            # plot_ss(ds.time, float(ds.ss1), ds.ss1_t, f"{filename}_1")
            # # plot_ss(ds.time, float(df_interpolated.ss2.iloc[0]), df_interpolated.ss2_t, f"{filename}_2")
            # plot_ss(ds.time, float(ds.ss3), ds.ss3_t, f"{filename}_3")
            
            # # make example plots for 53298_y2005 by running by hand for only this dataset, pausing
            # # code, and then running the following code and rerunning since changing o makes it so you 
            # # can't run the other plots.
            # # Example of when the sep distance is high
            # val = 84
            # o.history = o.history[:,:val+1]
            # ax, fig = o.plot(fast=True, land_color='#F0EFE4')
            # ax = add_drifter_track_to_plot(ax, df_interpolated.iloc[:val+1], transform=ccrs.PlateCarree(globe=crs.globe), color='r', linewidth=2, marker="o", markersize=10, label="In situ drifter" )
            # ax = add_feature_to_plot(ax, boundary_geom, ccrs.PlateCarree(globe=crs.globe), edgecolor='k', linestyle='--', facecolor='none')
            # time = ds.time[val].values
            # # valid_indices = ds.longitude.sel(time=time).notnull() & ds.latitude.sel(time=time).notnull()
            # # qhull = calc_qhull(ds.longitude.sel(time=time)[valid_indices], ds.latitude.sel(time=time)[valid_indices])
            # # ax = add_feature_to_plot(ax, Polygon(qhull), ccrs.PlateCarree(globe=crs.globe), edgecolor='b', facecolor='none', zorder=20, linewidth=2)
            # # Draw the line between the drifter and the qhull
            # lonnow, latnow = df_interpolated.cf["longitude"].iloc[val], df_interpolated.cf["latitude"].iloc[val]
            # lonmax, latmax = ds.cf["longitude"].isel(time=val).sel(drifters=922), ds.cf["latitude"].isel(time=val).sel(drifters=922)
            # # nearest_point = calc_distance_drifter_qhull(lonnow, latnow, qhull, return_nearest_point=True)
            # drifter_point, maxpoint = Point(lonnow, latnow), Point(lonmax, latmax)
            # ax = add_feature_to_plot(ax, LineString([drifter_point, maxpoint]), ccrs.PlateCarree(globe=crs.globe), edgecolor=col_other, facecolor='none', zorder=20, linewidth=1, linestyle='--')
            # ax = add_drifter_track_to_plot(ax, ds.isel(time=slice(None,val+1)).sel(drifters=922), transform=ccrs.PlateCarree(globe=crs.globe), color=col_max, linewidth=2, marker="o", markersize=10, label="Min sep distance", zorder=20)
            # ax = add_drifter_track_to_plot(ax, ds.isel(time=slice(None,val+1)).sel(drifters=38), transform=ccrs.PlateCarree(globe=crs.globe), color=col_mean, linewidth=2, marker="o", markersize=10, label="Mean sep distance", zorder=20)
            # # add a few example drifter locations along the line as markers, then lines across
            # dss = ds.isel(time=slice(None,val+1,15)).sel(drifters=922).dropna(dim="time")
            # df_ints = df_interpolated[:val+1:15].dropna(subset=df_interpolated.cf["longitude"].name)
            # ax.plot(dss.cf["longitude"], dss.cf["latitude"], transform=ccrs.PlateCarree(globe=crs.globe), color=col_max, marker="o", markersize=6, zorder=20, linewidth=0)
            # ax.plot(df_ints.cf["longitude"], df_ints.cf["latitude"], transform=ccrs.PlateCarree(globe=crs.globe), color="r", marker="o", markersize=6, zorder=20, linewidth=0)
            # # ax = add_drifter_track_to_plot(ax, dss, transform=ccrs.PlateCarree(globe=crs.globe), color=col_max, marker="o", markersize=6, zorder=20)
            # # lonsmax, latsmax = dss["longitude"].dropna(dim="time").values, dss["latitude"].dropna(dim="time").values
            # # for lonmax, latmax in zip(lonsmax, latsmax):
            # for timeearlier in dss.time.values:
            #     lonear, latear = df_ints.cf["longitude"].loc[timeearlier], df_ints.cf["latitude"].loc[timeearlier]
            #     lonsmax, latsmax = dss["longitude"].sel(time=timeearlier).values, dss["latitude"].sel(time=timeearlier).values
            #     drifter_point, nextpt = Point(lonear, latear), Point(lonsmax, latsmax)
            #     # import pdb; pdb.set_trace()
            #     ax = add_feature_to_plot(ax, LineString([drifter_point, nextpt]), ccrs.PlateCarree(globe=crs.globe), edgecolor=col_other, facecolor='none', zorder=20, linewidth=1, linestyle='--')
            # ax.set_title("Example to demonstrate the separation distance-based drifter metric")
            # ax.legend()
            # fig.savefig(f"{filename}_example_sep_max.png", bbox_inches='tight')
            # import pdb; pdb.set_trace()


            # # make example plots for 53298_y2005 by running by hand for only this dataset, pausing
            # # code, and then running the following code and rerunning since changing o makes it so you 
            # # can't run the other plots.
            # # Example of when the spread of the area covered by the drifters at this time step is larger than the shortest
            # # distance between the area and the in situ drifter
            # # qhull example
            # val = 79
            # o.history = o.history[:,:val+1]
            # ax, fig = o.plot(fast=True, land_color='#F0EFE4')
            # ax = add_drifter_track_to_plot(ax, df_interpolated.iloc[:val+1], transform=ccrs.PlateCarree(globe=crs.globe), color='r', linewidth=2, marker="o", markersize=10, label="In situ drifter" )
            # ax = add_feature_to_plot(ax, boundary_geom, ccrs.PlateCarree(globe=crs.globe), edgecolor='k', linestyle='--', facecolor='none')
            # time = ds.time[val].values
            # valid_indices = ds.longitude.sel(time=time).notnull() & ds.latitude.sel(time=time).notnull()
            # qhull = calc_qhull(ds.longitude.sel(time=time)[valid_indices], ds.latitude.sel(time=time)[valid_indices])
            # ax = add_feature_to_plot(ax, Polygon(qhull), ccrs.PlateCarree(globe=crs.globe), edgecolor='b', facecolor='none', zorder=20, linewidth=2)
            # # Draw the line between the drifter and the qhull
            # lonnow, latnow = df_interpolated.cf["longitude"].iloc[val], df_interpolated.cf["latitude"].iloc[val]
            # nearest_point = calc_distance_drifter_qhull(lonnow, latnow, qhull, return_nearest_point=True)
            # drifter_point = Point(lonnow, latnow)
            # ax = add_feature_to_plot(ax, LineString([drifter_point, nearest_point]), ccrs.PlateCarree(globe=crs.globe), edgecolor='b', facecolor='none', 
            #                          zorder=20, linewidth=2, linestyle='--')
            # ax.set_title("Example to demonstrate the area-based drifter metric")
            # ax.legend()
            # fig.savefig(f"{filename}_example_qhull_max.png", bbox_inches='tight')
            # import pdb; pdb.set_trace()


            if not os.path.exists(f"{basedir}/{filename}.png"):
                
                # title including start time, end time, dataset_id, depth, and model
                title = f"Drifter id: {dataset_id} ({slug_names[drifter_slug]}), run with {model}" \
                        f"\n{start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}, {float(df.cf['Z'][0])} m depth"
                        # f"\n{start_time.isoformat()[:16]} to {end_time.isoformat()[:16]}, {float(df.cf['Z'][0])} m depth"


                #     plt.title('%s\n%s to %s UTC (%i steps)' %
                #               (self._figure_title(),
                #                self.start_time.strftime('%Y-%m-%d %H:%M'),
                #                self.time.strftime('%Y-%m-%d %H:%M'),
                #                len(self.result.time)))
                # else:
                #     plt.title(
                #         '%s\n%i elements seeded at %s UTC' %
                #         (self._figure_title(), self.num_elements_scheduled(),
                #          self.elements_scheduled_time[0].strftime(
                #              '%Y-%m-%d %H:%M')))


                ax, fig = o.plot(fast=True, land_color='#F0EFE4', title=title)
                ax = add_drifter_track_to_plot(ax, df_interpolated, transform=ccrs.PlateCarree(globe=crs.globe), color='r', linewidth=2, marker="o", markersize=10, label="In situ drifter", zorder=20)
                ax = add_feature_to_plot(ax, boundary_geom, ccrs.PlateCarree(globe=crs.globe), edgecolor='k', linestyle='--', facecolor='none')
                ax.legend()
                fig.savefig(f"{basedir}/{filename}.png", bbox_inches='tight')
                
                # add plots of min and mean sep distance drifters
                if dataset_id == "53298_y2005":
                    ax = add_drifter_track_to_plot(ax, ds.sel(drifters=922), transform=ccrs.PlateCarree(globe=crs.globe), color=col_max, linewidth=2, marker="o", markersize=10, label="Min sep distance", zorder=20)
                    ax = add_drifter_track_to_plot(ax, ds.sel(drifters=38), transform=ccrs.PlateCarree(globe=crs.globe), color=col_mean, linewidth=2, marker="o", markersize=10, label="Mean sep distance", zorder=20)
                    ax.legend()
                    fig.savefig(f"{basedir}/{filename}_example.png", bbox_inches='tight')
        
                plt.close(fig)

            # # Animation
            # # plot the depth because it will always plot it masked with land_binary_mask
            # if not os.path.exists(f"{basedir}/{filename}.mp4"):
            #     o.animation(color='z', filename=f"{basedir}/{filename}.mp4", fast=True, fps=4, cmap=cmo.deep, land_color='#F0EFE4')
            
            # # Histogram plot
            # ax, fig = ptm.plotting.plot_dest(o, itime=-1, land_color='#F0EFE4')
            # ax.plot(df_interpolated.cf["longitude"].iloc[-1], df_interpolated.cf["latitude"].iloc[-1], color='r', marker="o", markersize=10, transform=ccrs.PlateCarree(globe=crs.globe))
            # # ax, fig = ptm.plotting.plot_dest(o, itime="all", land_color='#F0EFE4')
            # # lonbin, latbin = get_lonlat_bins(pixelsize_m=5000)
            # fig.savefig(f"{basedir}/{filename}_dest", bbox_inches='tight')
            # plt.close(fig)
            
            
