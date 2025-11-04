
import numpy as np
from scipy.spatial import ConvexHull
import shapely.geometry
import pandas as pd
from geopy.distance import geodesic
import pyproj
from shapely.ops import transform
import xarray as xr
from cartopy.feature import ShapelyFeature

col_max = "#8e44ad"
col_mean = "#63ad44"
col_other = "#ff5733"


def calc_total_distance(df):
    """Calculate the total distance traveled by the drifter in a DataFrame

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing the drifter positions.
    
    Returns
    -------
    array
        Array of distances between each pair of consecutive points.
    int
        Total distance traveled by the drifter in kilometers.
    """
    # Calculate the distance between each pair of consecutive points
    distances = np.array([geodesic((df.cf["latitude"].iloc[i], df.cf["longitude"].iloc[i]), 
                          (df.cf["latitude"].iloc[i+1], df.cf["longitude"].iloc[i+1])).kilometers
                 for i in range(len(df)-1)])
    # import pdb; pdb.set_trace()

    # nan out any zeros since this is used to divide
    distances[distances == 0] = np.nan
    
    distances = np.insert(distances, 0, 0)  # insert a 0 at the beginning for the first point
    
    return distances
    
    # # Sum the distances to calculate the total distance traveled
    # total_distance = np.sum(distances)
    # df["dist_along [km]"] = np.nan
    # # df.loc[:,"dist_along [km]"] = np.nan

    # # if len(distances) == 0:
    # #     return df["dist_along [km]"]
    
    # # else:
    # df["dist_along [km]"].iloc[1:] = distances
    # df["dist_along [km]"].iloc[0] = 0
    # # df.iloc[1:]["dist_along [km]"] = distances
    # # df.iloc[0]["dist_along [km]"] = 0

    # return df["dist_along [km]"]#, total_distance


def calc_qhull(lons, lats) -> shapely.geometry.Polygon:
    """Calculate the convex hull of the simulated drifter positions at a given time step

    Parameters
    ----------
    lons : _type_
        _description_
    lats : _type_
        _description_
    
    Returns
    -------
    shapely.geometry.Polygon
        Qhull of the simulated drifter positions at a given time step.
    """
    # Combine longitude and latitude into a single array of points
    points = np.column_stack((lons, lats))
    
    # Calculate the convex hull using SciPy
    hull = ConvexHull(points)
    
    # Extract the vertices of the convex hull
    hull_points = points[hull.vertices]
    
    # Create a Shapely polygon from the hull points
    hull_polygon = shapely.geometry.Polygon(hull_points)
    
    return hull_polygon


def calc_distance_drifter_qhull(lon, lat, qhull, return_nearest_point=False) -> float:
    """Calculate the distance between the drifter position and the Qhull of the simulated drifter position envelope at a given time step

    Parameters
    ----------
    lon, lat : _type_
        _description_
    qhull : _type_
        _description_
    
    Returns
    -------
    float
        Distance between the drifter position and the Qhull of the simulated drifter position envelope at a given time step.
    """
    # Calculate the distance between the drifter position and the Qhull of the simulated drifter position envelope
    point = shapely.geometry.Point(lon, lat)
    distance = qhull.distance(point)
    # print(distance)  # this is in deg
    if distance == 0:
        return 0
    
    # Otherwise convert the distance to kilometers
    # Find the nearest point on the Qhull boundary
    # nearest_point = qhull.boundary.interpolate(point)
    nearest_point = qhull.boundary.interpolate(qhull.boundary.project(point))
    if return_nearest_point:
        return nearest_point
    
    # Calculate the distance between the drifter position and the nearest point on the Qhull boundary
    distance = geodesic((lat, lon), (nearest_point.y, nearest_point.x)).kilometers
    # print(distance)
    return distance

def calc_qhull_area(qhull: shapely.geometry.Polygon) -> float:
    """Calculate the area of the Qhull in square kilometers.

    Parameters
    ----------
    qhull : shapely.geometry.Polygon
        Qhull of the simulated drifter position envelope.
    
    Returns
    -------
    float
        Area of the Qhull in square kilometers.
    """
    # Define the projection to convert lat/lon to meters
    proj_wgs84 = pyproj.CRS('EPSG:4326')  # WGS84 coordinate system
    proj_albers = pyproj.CRS('EPSG:5070')  # NAD83 / Conus Albers (equal-area projection)

    # Project the Qhull to the Albers Equal Area coordinate system
    project = pyproj.Transformer.from_crs(proj_wgs84, proj_albers, always_xy=True).transform
    qhull_albers = transform(project, qhull)

    # Calculate the area in square meters
    area_meters = qhull_albers.area
    
    # Convert the area to square kilometers
    area_meters /= 1e6
    
    return area_meters


# calculate the sum of the distance between the in situ drifter position at this time step and
# each simulated drifter position at this time step
# def calc_separation_distance(ds, df):
def calc_separation_distance_num(lons, lats, londf, latdf):
    """For one time, just numerator. Also per simulated drifter as an array without summing.
    
    

    Parameters
    ----------
    lons : _type_
        _description_
    lats : _type_
        _description_
    londf : _type_
        _description_
    latdf : _type_
        _description_
    
    Returns
    -------
    int
        Shape ndrifters (1000,) for one time step
    """
    
    # Calculate the distance between the in situ drifter position and each simulated drifter position
    distances = [geodesic((latdf, londf), (lats[j], lons[j])).kilometers
                 for j in range(len(lons))]

    # Sum the distances to calculate the total distance
    numerator = xr.DataArray(distances, dims=["drifters"], coords={"time": lons.time})
    # numerator = np.array(distances)
    
    return numerator


# def calc_separation_distance_num(lons, lats, londf, latdf):
#     """For one time, just numerator, but across all drifters

#     Parameters
#     ----------
#     lons : _type_
#         _description_
#     lats : _type_
#         _description_
#     londf : _type_
#         _description_
#     latdf : _type_
#         _description_
    
#     Returns
#     -------
#     int
#         _description_
#     """
    
#     # Calculate the distance between the in situ drifter position and each simulated drifter position
#     distances = [geodesic((latdf, londf), (lats[j], lons[j])).kilometers
#                  for j in range(len(lons))]
    
#     # Sum the distances to calculate the total distance
#     numerator = np.sum(distances)/len(lons)
    
#     # # df_dist["dist_along [km]"].sum(skipna=True)
#     # denominator = 0
#     # for i in range(len(df_dist)):  # this has length of times
#     #     for k in range(i):
#     #         denominator += df_dist[:k].sum(skipna=True)
            
#     # # this should simplify to the following
    
    
#     return numerator


def calc_separation_distance(df_interpolated, ds):
    """Combine previously calculated numerator and denominator
    
    to get the cumulative calulculations for the separation distance.
    """
    P = len(df_interpolated)
    num = ds["d"].sum(dim="time")
    # num = ds["d"].sum()
    denom = np.nansum([df_interpolated["dist_along [km]"].iloc[i]*(P-i) for i in range(P)])
    # if denom == 0:
    #     import pdb; pdb.set_trace()
    # # if (num/denom).isnull().any():# or denom.isnull.all():
    # #     import pdb; pdb.set_trace()
    # # num/denom is getting smaller each time step from beginning
    return num/denom
    

def calc_ss(df, o):
    """_summary_

    Parameters
    ----------
    df : _type_
        _description_
    o : OpenDrift object
        _description_
    """
    # 1 - 1/N * sum over time steps of (distance between the drifter position at that time and the Qhull of the simulated drifter position envelope at that time / sqrt of (the area of the Qhull of the simulated drifter tracks
    
    # first align the drifter and model time steps
    # model times: pd.date_range(o.start_time.isoformat(), o.end_time.isoformat(), periods=o.steps_output)
    # model positions: o.history["lon"].data, o.history["lat"].data
    lons, lats = o.result["lon"].values, o.result["lat"].values
    # have to add 40min to start_time due to the range of times I am using!
    # in order to align with the in situ drifter times
    model_times = pd.DatetimeIndex([pd.Timestamp(t) for t in o.result.time.values])
    # make a Dataset out of model output to track times correctly
    ds = xr.Dataset({"time": model_times, 
                     "longitude": (["time","drifters"], lons.T), 
                     "latitude": (["time","drifters"], lats.T),
                     "d": (["time","drifters"], np.zeros(lats.T.shape)*np.nan),
                     "Dist to qhull [km]": (["time"], np.zeros(len(model_times))*np.nan),
                     "Qhull area [km^2]": (["time"], np.zeros(len(model_times))*np.nan),
                     "separation_distance": (["time","drifters"], np.zeros(lats.T.shape)*np.nan),
                     })

    try:
        df.cf["T"] = pd.to_datetime(df.cf["T"])
    except ValueError:
        # for lake clark drifters
        # import pdb; pdb.set_trace()
        df.cf["T"] = pd.to_datetime(df.cf["T"], dayfirst=True, format='mixed')
        # df.cf["T"] = pd.to_datetime(df.cf["T"], format="%d-%b-%Y %H:%M:%S")

    # Ensure there are no duplicate labels in the index
    df = df.drop_duplicates(subset=[df.cf["T"].name])
    # ensure no duplicate positions in drifter location
    df = df.drop_duplicates(subset=[df.cf["longitude"].name, df.cf["latitude"].name])

    # Interpolate the DataFrame to the model times
    # all_times = model_times.union([pd.Timestamp(t) for t in df.cf["T"]]).sort_values()
    # don't want the model time to be outside the drifter time range bc then get a
    # nan in df_interpolated that propagates. So, leave off initial model times before drifter
    # start time
    model_times = model_times[model_times >= df.cf["T"].min()]

    all_times = model_times.union(df.cf["T"])

    all_times = all_times.drop_duplicates()#subset=[df.cf["T"].name])

    # Set the index, reindex, and interpolate
    df_interpolated = df.set_index(df.cf["T"].name, drop=True).reindex(all_times).interpolate().reindex(model_times)#.dropna(subset=df.cf["longitude"].name)
    
    # # if initial model time is before initial drifter time, need to back fill to
    # # avoid nans in the next calculation
    # if df_interpolated.longitude.isnull().iloc[0]:
    #     df_interpolated = df_interpolated.bfill()

    # then loop over the simulation time steps and for each time step calculate 
    # the distance between the drifter position and the Qhull of the simulated drifter position envelope at that time
    # also calculate the distance between the in situ drifter position at this time step and 
    #  each simulated drifter position at that time step
    # dists, areas = np.zeros(lons.shape[1]), np.zeros(lons.shape[1])
    # dist_simulated_to_in_situ = np.zeros(lons.shape[1])
    
    # df_interpolated["Dist to qhull [km]"] = np.nan
    # df_interpolated["Qhull area [km^2]"] = np.nan
    # df_interpolated["separation_distance"] = np.nan
    
    # dfsep = pd.DataFrame(index=model_times, columns=["d", "l"])
    # import pdb; pdb.set_trace()
    df_interpolated["dist_along [km]"] = calc_total_distance(df_interpolated.dropna(subset=df.cf["longitude"].name).copy())
    
    # for time in df_interpolated.index:
    for i, time in enumerate(model_times):
        # import pdb; pdb.set_trace()
        # time = time.values
        # print(time)
        
        if ds.longitude.sel(time=time).notnull().sum() <= 2 or ds.latitude.sel(time=time).notnull().sum() <= 2:
            continue
        
        # Filter out NaN values
        valid_indices = ds.longitude.sel(time=time).notnull() & ds.latitude.sel(time=time).notnull()
        try:
            qhull = calc_qhull(ds.longitude.sel(time=time)[valid_indices], ds.latitude.sel(time=time)[valid_indices])
        except:
            import pdb; pdb.set_trace()
                
        # this qhull is valid at a specific time. Find the corresponding time
        # in df_interpolated to send that row into the function.
        londf = df_interpolated.cf["longitude"].loc[time]
        latdf = df_interpolated.cf["latitude"].loc[time]
        
        # model time might start before drifter time
        if np.isnan(londf) and np.isnan(latdf):
            continue
        
        ds["Dist to qhull [km]"].loc[dict(time=time)] = calc_distance_drifter_qhull(londf, latdf, qhull)
        ds["Qhull area [km^2]"].loc[dict(time=time)] = calc_qhull_area(qhull)

        # df_interpolated.loc[time, "Dist to qhull [km]"] = calc_distance_drifter_qhull(londf, latdf, qhull)
        # df_interpolated.loc[time, "Qhull area [km^2]"] = calc_qhull_area(qhull)

        # calculate the sum of the distance between the in situ drifter position at this time step and
        # each simulated drifter position at this time step
        # this is an average (should it be?)

        # df_interpolated.loc[time, "separation_distance"] = calc_separation_distance(ds.sel(time=time), df_interpolated.loc[time])
        
        if time == model_times[0] or (np.isnan(df_interpolated.cf["longitude"].loc[model_times[i-1]]) \
                                  and np.isnan(df_interpolated.cf["latitude"].loc[model_times[i-1]])):
        # if time == ds.time[0] or (np.isnan(df_interpolated.cf["longitude"].loc[ds.time[i-1].values]) \
        #                           and np.isnan(df_interpolated.cf["latitude"].loc[ds.time[i-1].values])):
            ds["d"].loc[dict(time=time)] = 0
            ds["separation_distance"].loc[dict(time=time)] = 0
            # df_interpolated.loc[time, "d"] = 0
            # df_interpolated.loc[time, "separation_distance"] = 0
        else:

            # df_interpolated.loc[time, "separation_distance"] = calc_separation_distance(ds.sel(time=slice(None,time)),
            #                                                                                 df_interpolated.loc[:time])
            ds["d"].loc[dict(time=time, drifters=valid_indices)] = calc_separation_distance_num(ds.longitude.sel(time=time)[valid_indices], 
                                                                        ds.latitude.sel(time=time)[valid_indices], 
                                                                        londf, latdf)
            # ds["d"] = separation_distance_num  # might have to assign this after has full time slice
            # ds = ds.loc[dict(time=time)].assign(d=separation_distance_num)
            # df_interpolated.loc[time, "d"] = calc_separation_distance_num(ds.longitude.sel(time=time), 
            #                                                             ds.latitude.sel(time=time), 
            #                                                             londf, latdf)
            # df_interpolated.loc[time, "d"] = calc_separation_distance_num(ds.longitude.sel(time=time)[valid_indices], 
            #                                                             ds.latitude.sel(time=time)[valid_indices], 
            #                                                             londf, latdf)
            # dfsep.loc[time, "l"] = calc_separation_distance_denom(ds.longitude.sel(time=time)[valid_indices], 
            #                                                             ds.latitude.sel(time=time)[valid_indices], 
            #                                                             londf, latdf)
            #                                                             # calc_total_distance(df_interpolated.loc[:time]))
            # df_interpolated.loc[time, "separation_distance"] = calc_separation_distance(df_interpolated.loc[:time].iloc[1:])
            
            # if df_interpolated.loc[:time].iloc[1:]["dist_along [km]"].isnull().all():
            #     import pdb; pdb.set_trace()
            ds["separation_distance"].loc[dict(time=time)] = calc_separation_distance(df_interpolated.loc[:time].iloc[1:], ds.sel(time=slice(None,time)).isel(time=slice(1,None)))
            # ds.loc[dict(time=time)]["separation_distance"] = calc_separation_distance(df_interpolated.loc[:time].iloc[1:], ds)

        # valid_indices = ~np.isnan(lons[:, i]) & ~np.isnan(lats[:, i])
        # qhull = calc_qhull(lons[valid_indices,i], lats[valid_indices,i])
        # # this qhull is valid at a specific time. Find the corresponding time
        # # in df to send that row into the function.
        # londf = df_interpolated.cf["longitude"].loc[model_times[i]]
        # latdf = df_interpolated.cf["latitude"].loc[model_times[i]]
        # dist = calc_distance_drifter_qhull(londf, latdf, qhull)
        # # sums[i] = dist/np.sqrt(qhull.area)
        # dists[i] = dist
        # areas[i] = calc_qhull_area(qhull)
        # # areas[i] = qhull.area
        
        # # calculate the sum of the distance between the in situ drifter position at this time step and
        # # each simulated drifter position at this time step
        # # this is an average (should it be?)
        # dist_simulated_to_in_situ[i] = calc_separation_distance(lons[valid_indices,i], lats[valid_indices,i], londf, latdf)
    
    # for i in range(lons.shape[1]):
    #     # might be before the first or after the last time in the df
    #     if np.isnan(df_interpolated.loc[model_times[i]][df.cf["longitude"].name]):
    #         continue
    #     else:
            # # Filter out NaN values
            # valid_indices = ~np.isnan(lons[:, i]) & ~np.isnan(lats[:, i])
            # qhull = calc_qhull(lons[valid_indices,i], lats[valid_indices,i])
            # # this qhull is valid at a specific time. Find the corresponding time
            # # in df to send that row into the function.
            # londf = df_interpolated.cf["longitude"].loc[model_times[i]]
            # latdf = df_interpolated.cf["latitude"].loc[model_times[i]]
            # dist = calc_distance_drifter_qhull(londf, latdf, qhull)
            # # sums[i] = dist/np.sqrt(qhull.area)
            # dists[i] = dist
            # areas[i] = calc_qhull_area(qhull)
            # # areas[i] = qhull.area
            
            # # calculate the sum of the distance between the in situ drifter position at this time step and
            # # each simulated drifter position at this time step
            # # this is an average (should it be?)
            # dist_simulated_to_in_situ[i] = calc_separation_distance(lons[valid_indices,i], lats[valid_indices,i], londf, latdf)
    ds["ss1_t"] = ds["Dist to qhull [km]"]/np.sqrt(ds["Qhull area [km^2]"])
    ds["ss1"] = 1 - ds["ss1_t"].sum(skipna=True)/lons.shape[1]
    # df_interpolated["ss1_t"] = df_interpolated["Dist to qhull [km]"]/np.sqrt(df_interpolated["Qhull area [km^2]"])
    # df_interpolated["ss1"] = 1 - df_interpolated["ss1_t"].sum(skipna=True)/lons.shape[1]
    # df_interpolated["ss1"] = 1 - (df_interpolated["Dist to qhull [km]"]/np.sqrt(df_interpolated["Qhull area [km^2]"])).sum(skipna=True)#/lons.shape[1]
    # sums = dists/np.sqrt(areas)


    
    # dist_along_df_interpolated, total_dist_df_interpolated = calc_total_distance(df_interpolated.dropna(subset=df.cf["longitude"].name))

    # df_interpolated["ss2_t"] = df_interpolated["Dist to qhull [km]"]/df_interpolated["dist_along [km]"]
    # df_interpolated["ss2"] = 1 - df_interpolated["ss2_t"].sum(skipna=True)#/lons.shape[1]


    # this is the separation distance
    
    # Save the best separation distance resulting in the best SS
    
    # df_interpolated["ss3_t"] = df_interpolated["separation_distance"]#/df_interpolated["dist_along [km]"]
    # df_interpolated["ss3_t"] = df_interpolated["separation_distance"]/df_interpolated["dist_along [km]"]
    
    # take last separation distance for skill score
    
    
    # Could define max/mean skill scores based on the minimized separation distance
    # across the whole time series
    ntimes = len(ds.time)
    
    rms_sep_dist = np.sqrt((ds["separation_distance"]**2).sum(dim="time")/ntimes)

    # use index of min cumulative separation distance to find corresponding drifter track
    imin = rms_sep_dist.argmin()
    # integrated max skill score over drifter time period (should be closest to in situ drifter)
    # as opposed to at the end of the simulation
    ds["ss3_int_max"] = float(1 - rms_sep_dist[imin])
    ds["ss3_int_max_t"] = ds["separation_distance"][:,imin]

    # find localmax that isn't the first one since that is from starting near the in situ drifter
    # from scipy.signal import argrelmax
    # argrelmax(ds["ss3_int_max_t"].values, order=15)  # example index -> 84

    # same for mean, but no short cut for that one
    imean = int(abs(rms_sep_dist - rms_sep_dist.mean()).argmin())
    ds["ss3_int_mean"] = float(1 - rms_sep_dist[imean])
    ds["ss3_int_mean_t"] = ds["separation_distance"][:,imean]

    ds["ss3_int_std"] = 1 - (rms_sep_dist).std()
    
    
    # cumulative_sep_dist = ds["separation_distance"].sum(dim="time")/ntimes
    # # use index of min cumulative separation distance to find corresponding drifter track
    # imin = cumulative_sep_dist.argmin()
    # # integrated max skill score over drifter time period (should be closest to in situ drifter)
    # # as opposed to at the end of the simulation
    # ds["ss3_int_max"] = float(1 - cumulative_sep_dist[imin]/ntimes)
    # ds["ss3_int_max_t"] = ds["separation_distance"][:,imin]

    # # same for mean, but no short cut for that one
    # imean = int(abs(cumulative_sep_dist - cumulative_sep_dist.mean()).argmin())
    # ds["ss3_int_mean"] = float(1 - cumulative_sep_dist[imean]/ntimes)
    # ds["ss3_int_mean_t"] = ds["separation_distance"][:,imean]

    # ds["ss3_int_std"] = 1 - (cumulative_sep_dist/ntimes).std()

    
    # Could define max/mean skill scores based on the final separation distance:
    skill_scores = 1 - ds["separation_distance"].dropna(dim="time")[-1]
    # use index of max skill score to find corresponding drifter track
    iss3_max = int(skill_scores.argmax())

    # same for mean skill score, but no short cut for that one
    iss3_mean = int(abs(skill_scores - skill_scores.mean()).argmin())
    
    # separation distance is both nondimensional and cumulative
    # so it isn't summed over time
    ds["ss3_max_t"] = ds["separation_distance"][:,iss3_max]
    ds["ss3_max"] = float(skill_scores[iss3_max])

    ds["ss3_mean_t"] = ds["separation_distance"][:,iss3_mean]
    ds["ss3_mean"] = float(skill_scores[iss3_mean])
    ds["ss3_std"] = float(skill_scores.std())
    
    
    
    # ds["ss3"] = 1 - ds["ss3_t"]#.sum(skipna=True)#/lons.shape[1]
    
    return ds, df_interpolated

    # nan out any zeros
    # izeros = list(set(np.arange(len(dist_along_df_interpolated))) - set(np.nonzero(dist_along_df_interpolated)[0]))
    # dist_along_df_interpolated[izeros] = np.nan
    # dist_along_df_interpolated[dist_along_df_interpolated == 0] = np.nan

    # separation_distance = dist_simulated_to_in_situ[1:]/dist_along_df_interpolated
    # divide by times (1/N) (might be off by 1 for a missing time)
    # ss = 1 - np.nansum(sums)/lons.shape[1]
    # ss2 = 1 - np.nansum(dists)/(total_dist_df_interpolated)
    # ss2 = 1 - np.nansum(dists)/(lons.shape[1]*total_dist_df_interpolated)
    # ss3 = 1 - np.nansum(separation_distance)
    # return model_times, ss, sums, ss2, dists, df_interpolated, dist_simulated_to_in_situ[1:], dist_along_df_interpolated, separation_distance, ss3

def plot_ss_qhull(ds, filename):
    """Plot the SS metric over time

    Parameters
    ----------
    model_times : _type_
        _description_
    ss : _type_
        _description_
    """
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 4))
    plt.plot(ds.time, ds["ss1_t"], color=col_max)
    # xlim = plt.xlim()
    ylim = plt.ylim()
    # import pdb; pdb.set_trace()
    plt.hlines(1, ds.time[0], ds.time[-1], color="k", linestyle="--", lw=0.2)
    # plt.xlabel("Time")
    if "53298_y2005" in filename:
        val = 79
        plt.vlines(ds["ss1_t"].time[val], *plt.ylim(), color="b", linestyle="--", lw=1)
    plt.xlim(ds.time[0], ds.time[-1])
    plt.ylim(*ylim)
    plt.ylabel("Competing length scales")
    plt.title(f"Distance to Qhull / sqrt(Qhull area), skill score: {ds.ss1:.2f}")
    plt.xticks(rotation=30)  # Rotate x-axis ticks by 45 degrees
    plt.show()
    plt.savefig(f"{filename}_ss_qhull.pdf", bbox_inches='tight')
    plt.savefig(f"{filename}_ss_qhull.png", bbox_inches='tight')
    plt.close()


def plot_ss_sep(ds, filename):
    """Plot the SS metric over time

    Parameters
    ----------
    model_times : _type_
        _description_
    ss : _type_
        _description_
    """
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 4))
    # plt.plot(ds.time, ds["ss3_max_t"], label="Max at end time")
    # plt.plot(ds.time, ds["ss3_mean_t"], label="Mean at end time")

    # start from localmin that isn't the first one for plot 
    from scipy.signal import argrelmin
    min = argrelmin(ds["ss3_int_max_t"].values, order=1)[0]
    if len(min) == 0:
        ind = 0
    else:
        ind = min[0]
    # import pdb; pdb.set_trace()
    # ind = argrelmin(ds["ss3_int_max_t"].values, order=15)[0][0]    
    plt.plot(ds.time[ind:], ds["ss3_int_max_t"][ind:], label="Min separation distance", color=col_max)
    min = argrelmin(ds["ss3_int_mean_t"].values, order=1)[0]
    if len(min) == 0:
        ind = 0
    else:
        ind = min[0]
    plt.plot(ds.time[ind:], ds["ss3_int_mean_t"][ind:], label="Mean separation distance", color=col_mean)
    plt.xlim(ds.time[0], ds.time[-1])
    if "53298_y2005" in filename:
        val = 84
        plt.vlines(ds["ss3_int_max_t"].time[val], *plt.ylim(), color=col_other, linestyle="--", lw=1)
    # plt.plot(ds.time, ds["ss3_int_max_t"], label="Max, integrated over simulation")
    # plt.plot(ds.time, ds["ss3_int_mean_t"], label="Mean, integrated over simulation")
    plt.legend(loc="best")

    plt.ylabel("Separation distance")
    plt.title(f"Separation distance, skill score: Max (min sep dist): {ds.ss3_int_max:.2f}, Mean: {ds.ss3_int_mean:.2f}, Std: {ds.ss3_int_std:.2f}")
    # plt.title(f"Sep distance, SS: Max end: {ds.ss3_max:.2f}, Mean end: {ds.ss3_mean:.2f}, Std end: {ds.ss3_std:.2f},/nMax int: {ds.ss3_int_max:.2f}, Mean int: {ds.ss3_int_mean:.2f}, , Std int: {ds.ss3_int_std:.2f}")
    plt.xticks(rotation=30)  # Rotate x-axis ticks by 45 degrees
    plt.show()
    plt.savefig(f"{filename}_ss_sep.pdf", bbox_inches='tight')
    plt.savefig(f"{filename}_ss_sep.png", bbox_inches='tight')
    plt.close()


# def plot_ss(model_times, ss, sums, filename):
#     """Plot the SS metric over time

#     Parameters
#     ----------
#     model_times : _type_
#         _description_
#     ss : _type_
#         _description_
#     """
#     import matplotlib.pyplot as plt
#     plt.plot(model_times, sums)
#     plt.xlabel("Time")
#     plt.ylabel("SS")
#     plt.title(f"SS metric over time. SS: {ss}")
#     plt.xticks(rotation=30)  # Rotate x-axis ticks by 45 degrees
#     plt.show()
#     plt.savefig(f"{filename}_ss.pdf", bbox_inches='tight')
#     plt.close()


def add_drifter_track_to_plot(ax, df_interpolated, transform, **kwargs):
# def add_drifter_track_to_plot(ax, df_interpolated, transform, color, linewidth, marker, markersize, label, zorder=None):
    # add drifter track
    kwargs_no_label = kwargs.copy()
    kwargs_no_label.pop("label")
    if isinstance(df_interpolated, (pd.DataFrame, pd.Series)):
        ax.plot(df_interpolated.cf["longitude"].iloc[-1], df_interpolated.cf["latitude"].iloc[-1], 
                transform=transform, **kwargs_no_label)
    elif isinstance(df_interpolated, xr.Dataset):
        ax.plot(df_interpolated.cf["longitude"][-1], df_interpolated.cf["latitude"][-1], 
                transform=transform, **kwargs_no_label)
    kwargs.pop("marker")
    ax.plot(df_interpolated.cf["longitude"], df_interpolated.cf["latitude"], transform=transform, **kwargs)
    ax.autoscale()
    return ax


def add_feature_to_plot(ax, boundary_geom, transform, **kwargs):
    # add domain boundary
    shape_feature = ShapelyFeature([boundary_geom], transform, **kwargs)
    ax.add_feature(shape_feature, **kwargs)
    return ax