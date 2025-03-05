import matplotlib.pyplot as plt
import numpy as np
from ridge_map import RidgeMap
from rasterio.mask import mask
from shapely.geometry import box
import rasterio

def create_ridge_plot_optimized(values, title=None, max_lines=200):
    """Create ridge map"""
    try:
        values = np.flipud(values)
        values = np.nan_to_num(values, nan=np.nanmean(values))
        
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
        
        return fig
        
    except Exception as e:
        return None

def create_adjusted_ridge_plot(tiff_path, requested_bounds, title=None):
    """Create ridge plot for an adjusted region"""
    try:
        # Create bounding box and get adjusted image
        bbox = box(*requested_bounds)
        
        # Re-open the TIFF file to use mask operation
        with rasterio.open(tiff_path) as src:
            # Get adjusted image using mask operation
            out_image, out_transform = mask(src, [bbox], crop=True)
            
            if out_image.size > 0:
                return create_ridge_plot_optimized(out_image[0], title)
            else:
                return None
                
    except Exception as e:
        return None 