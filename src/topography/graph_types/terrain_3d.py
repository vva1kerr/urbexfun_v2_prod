import numpy as np
import plotly.graph_objects as go
from rasterio.mask import mask
from shapely.geometry import box
import rasterio

def downsample_for_3d(data, max_points=100):
    """
    Downsample data for 3D plotting to improve performance.
    
    Args:
        data: numpy array of elevation data
        max_points: maximum number of points in each dimension
        
    Returns:
        Downsampled numpy array
    """
    if data.shape[0] <= max_points and data.shape[1] <= max_points:
        return data
        
    # Calculate downsampling factor
    factor = min(data.shape[0] // max_points, data.shape[1] // max_points)
    if factor < 1:
        factor = 1
        
    # Downsample the data
    return data[::factor, ::factor]

def create_3d_plot(data, bounds):
    """Create 3D terrain plot"""
    try:
        # Flip the data array vertically to correct orientation
        data = np.flipud(data)
        
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
            # title='3D Terrain View',
            scene=dict(
                xaxis_title='Longitude',
                yaxis_title='Latitude',
                zaxis_title='Elevation (m)',
                camera=dict(
                    eye=dict(x=-1.0, y=-1.0, z=1.0)
                )
            ),
            width=600,
            height=600
        )
        
        return fig
        
    except Exception as e:
        return None

def create_adjusted_3d_plot(tiff_path, requested_bounds):
    """Create 3D plot for an adjusted region"""
    try:
        # Create bounding box and get adjusted image
        bbox = box(*requested_bounds)
        
        # Re-open the TIFF file to use mask operation
        with rasterio.open(tiff_path) as src:
            # Get adjusted image using mask operation
            out_image, out_transform = mask(src, [bbox], crop=True)
            
            if out_image.size > 0:
                # Create a bounds object for the adjusted region
                adjusted_bounds_obj = type('Bounds', (), {
                    'left': requested_bounds[0],
                    'right': requested_bounds[2],
                    'bottom': requested_bounds[1],
                    'top': requested_bounds[3]
                })
                
                return create_3d_plot(out_image[0], adjusted_bounds_obj)
            else:
                return None
                
    except Exception as e:
        return None 