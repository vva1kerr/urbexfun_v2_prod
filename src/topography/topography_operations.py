import rasterio
from rasterio.plot import show
from rasterio.windows import Window
import matplotlib.pyplot as plt
from shapely.geometry import box
from rasterio.mask import mask
from matplotlib.colors import LinearSegmentedColormap
from matplotlib import colors
from PIL import Image
import numpy as np
import pandas as pd
import os
from ridge_map import RidgeMap
import plotly.graph_objects as go
import gc
import psutil

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def check_memory_before_operation(operation_name, threshold_mb=1000):
    """Check if we have enough memory before a heavy operation"""
    current_memory = get_memory_usage()
    if current_memory > threshold_mb:
        gc.collect()
        current_memory = get_memory_usage()
        if current_memory > threshold_mb:
            return False
    return True

def clamp_bounds(requested_bounds, tiff_bounds):
    """
    Clamp requested bounds to stay within TIFF file bounds.
    Returns tuple of (min_lon, min_lat, max_lon, max_lat)
    """
    min_lon = max(min(requested_bounds[0], requested_bounds[2]), tiff_bounds.left)
    max_lon = min(max(requested_bounds[0], requested_bounds[2]), tiff_bounds.right)
    min_lat = max(min(requested_bounds[1], requested_bounds[3]), tiff_bounds.bottom)
    max_lat = min(max(requested_bounds[1], requested_bounds[3]), tiff_bounds.top)
    
    return (min_lon, min_lat, max_lon, max_lat)

def load_and_downsample_tiff(tiff_path, downsample_factor=2):
    """Load TIFF file with downsampling to manage memory"""
    try:
        with rasterio.open(tiff_path) as src:
            width = src.width
            height = src.height
            
            window_width = width // downsample_factor
            window_height = height // downsample_factor
            
            data = src.read(
                1,
                out_shape=(1, window_height, window_width),
                resampling=rasterio.enums.Resampling.average,
                masked=True
            )
            
            data = np.squeeze(data)
            
            if hasattr(data, 'mask'):
                data = data.filled(np.nan)
            
            gc.collect()
            
            return data, src.bounds
            
    except Exception as e:
        gc.collect()
        raise

def create_ridge_plot_optimized(values, title=None, max_lines=200):
    """Create ridge map with memory optimization"""
    try:
        values = np.flipud(values)
        values = np.nan_to_num(values, nan=np.nanmean(values))
        
        if values.shape[0] > max_lines:
            step = values.shape[0] // max_lines
            values = values[::step]
        
        fig, ax = plt.subplots(figsize=(10, 10))
        
        rm = RidgeMap()
        
        processed_values = rm.preprocess(
            values=values,
            lake_flatness=0.25,
            water_ntile=15,
            vertical_ratio=50
        )
        
        rm.plot_map(
            values=processed_values,
            label=title,
            ax=ax
        )
        
        ax.axis('off')
        plt.close('all')
        gc.collect()
        
        return fig
        
    except Exception as e:
        return None

def create_dem_plot(data, bounds, title=None):
    """Create DEM plot with memory optimization"""
    try:
        fig, ax = plt.subplots(figsize=(10, 10))
        
        im = ax.imshow(data, 
                      cmap='terrain',
                      extent=[bounds.left, bounds.right, 
                             bounds.bottom, bounds.top])
        
        plt.colorbar(im, ax=ax, label='Elevation (meters)')
        
        if title:
            ax.set_title(title)
        
        ax.xaxis.set_major_formatter(plt.FormatStrFormatter('%.2f°'))
        ax.yaxis.set_major_formatter(plt.FormatStrFormatter('%.2f°'))
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        
        plt.tight_layout()
        
        return fig
        
    except Exception as e:
        return None

def create_3d_plot(data, bounds):
    """Create 3D terrain plot with memory optimization"""
    try:
        y = np.linspace(bounds.bottom, bounds.top, data.shape[0])
        x = np.linspace(bounds.left, bounds.right, data.shape[1])
        X, Y = np.meshgrid(x, y)
        
        fig = go.Figure(data=[
            go.Surface(
                z=data,
                x=X,
                y=Y,
                colorscale='earth',
                name='Elevation'
            )
        ])

        fig.update_layout(
            title='3D Terrain View',
            scene=dict(
                xaxis_title='Longitude',
                yaxis_title='Latitude',
                zaxis_title='Elevation (m)',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.2)
                )
            ),
            width=600,
            height=600
        )
        
        return fig
        
    except Exception as e:
        return None

def downsample_for_3d(data, max_points=200000):
    """Downsample data for 3D plotting to prevent memory issues"""
    current_points = data.shape[0] * data.shape[1]
    if current_points > max_points:
        reduction_factor = int(np.sqrt(current_points / max_points))
        return data[::reduction_factor, ::reduction_factor]
    return data

def format_coordinates(lat, lon):
    """Format coordinates nicely with N/S and E/W indicators"""
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    return f"({abs(lat):.2f}°{lat_dir}, {abs(lon):.2f}°{lon_dir})"

def load_and_resize(image_path, width, height):
    """Resize image to fixed dimensions"""
    img = Image.open(image_path)
    return img.resize((width, height)) 