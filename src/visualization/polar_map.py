import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point
import numpy as np

def create_polar_plot(figsize=(8, 8)):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect('equal')
    ax.set_title("Antarctic Polar Trajectory (EPSG:3031)")
    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")
    ax.grid(True, linestyle='--', alpha=0.5)
    return fig, ax

def plot_trajectory_on_ax(ax, hist_x, hist_y, curr_x, curr_y, pred_x, pred_y, true_x=None, true_y=None, label_prefix=""):
    # Historical
    ax.plot(hist_x, hist_y, color='gray', linestyle='-', marker='.', alpha=0.6, label=f'{label_prefix} Historical Path')
    
    # Current
    ax.plot(curr_x, curr_y, color='black', marker='s', markersize=8, label=f'{label_prefix} Current Location')
    
    # Predicted
    if pred_x is not None and pred_y is not None:
        ax.plot([curr_x, pred_x], [curr_y, pred_y], color='red', linestyle='--', marker='X', markersize=8, label=f'{label_prefix} Predicted')
        
    # True
    if true_x is not None and true_y is not None:
        ax.plot([curr_x, true_x], [curr_y, true_y], color='green', linestyle='-', marker='*', markersize=8, label=f'{label_prefix} Ground Truth')
        
    ax.legend()

def wgs84_to_epsg3031(lons, lats):
    gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lons, lats), crs="EPSG:4326")
    gdf_3031 = gdf.to_crs("EPSG:3031")
    return gdf_3031.geometry.x.values, gdf_3031.geometry.y.values
