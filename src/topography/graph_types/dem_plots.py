import matplotlib.pyplot as plt
import numpy as np
from rasterio.mask import mask
from shapely.geometry import box
import rasterio

def create_dem_plot(data, bounds, title=None):
    """Create DEM plot"""
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

def create_adjusted_dem_plot(tiff_path, adjusted_bounds, bounds, title=None):
    """Create DEM plot for an adjusted region"""
    try:
        # Create bounding box and get adjusted image
        bbox = box(*adjusted_bounds)
        
        # Re-open the TIFF file to use mask operation
        with rasterio.open(tiff_path) as src:
            # Get adjusted image using mask operation
            out_image, out_transform = mask(src, [bbox], crop=True)
            
            if out_image.size > 0:
                # Create a bounds object for the adjusted region
                adjusted_bounds_obj = type('Bounds', (), {
                    'left': adjusted_bounds[0],
                    'right': adjusted_bounds[2],
                    'bottom': adjusted_bounds[1],
                    'top': adjusted_bounds[3]
                })
                
                return create_dem_plot(out_image[0], adjusted_bounds_obj, title)
            else:
                return None
                
    except Exception as e:
        return None 
    
if __name__ == "__main__":
    # Test the create_adjusted_dem_plot function
    tiff_path = rf"mnt/c/Users/foo/Desktop/1x1_tif_outputs/10_DEM_y20x-110/xmin-106.000417_xmax-105.000417_ymin20.999583_ymax21.999583.tif"
    adjusted_bounds = (left, bottom, right, top)  # Adjusted bounds in (left, bottom, right, top) format
    bounds = (left, bottom, right, top)  # Original bounds in (left, bottom, right, top) format
    title = "Adjusted DEM Plot"
    create_adjusted_dem_plot(tiff_path, adjusted_bounds, bounds, title)