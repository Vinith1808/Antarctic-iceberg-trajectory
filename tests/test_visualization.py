import pytest
import numpy as np
from src.visualization.polar_map import wgs84_to_epsg3031, create_polar_plot, plot_trajectory_on_ax

def test_wgs84_to_epsg3031():
    # Test origin
    lons = np.array([0.0])
    lats = np.array([-90.0])
    x, y = wgs84_to_epsg3031(lons, lats)
    assert np.isfinite(x[0])
    assert np.isfinite(y[0])
    
    # Check shape matching
    lons = np.array([-45.0, 45.0, 90.0])
    lats = np.array([-65.0, -70.0, -60.0])
    x, y = wgs84_to_epsg3031(lons, lats)
    assert len(x) == 3
    assert len(y) == 3
    assert all(np.isfinite(x))
    assert all(np.isfinite(y))

def test_create_polar_plot():
    fig, ax = create_polar_plot()
    assert fig is not None
    assert ax is not None
    assert ax.get_aspect() == 1.0 # 'equal'

def test_plot_trajectory_on_ax():
    fig, ax = create_polar_plot()
    hist_x = np.array([0, 10, 20])
    hist_y = np.array([0, 10, 20])
    plot_trajectory_on_ax(ax, hist_x, hist_y, 20, 20, 30, 30, 40, 40, "test")
    
    # Check that lines were added
    assert len(ax.lines) > 0
