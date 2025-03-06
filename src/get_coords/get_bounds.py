import rasterio
from rasterio.transform import from_origin
import numpy as np

def get_bounds_from_tif(tif_path):
    """
    Get the bounds of a .tif file
    
    Args:
        tif_path (str): Path to the .tif file
        
    Returns:
        tuple: (left, bottom, right, top) in the coordinate system of the file
        dict: Dictionary containing additional metadata about the bounds
    """
    try:
        with rasterio.open(tif_path) as src:
            # Get the bounds
            bounds = src.bounds
            
            # Get additional metadata
            metadata = {
                'width': src.width,
                'height': src.height,
                'crs': src.crs,
                'transform': src.transform,
                'nodata': src.nodata,
                'dtype': src.dtypes[0]
            }
            
            return bounds, metadata
            
    except Exception as e:
        print(f"Error reading bounds from {tif_path}: {str(e)}")
        return None, None

def print_bounds_info(bounds, metadata):
    """Print formatted information about the bounds and metadata"""
    if bounds is None:
        print("No bounds available")
        return
        
    print("\n=== Bounds Information ===")
    print(f"Left: {bounds.left:.6f}")
    print(f"Bottom: {bounds.bottom:.6f}")
    print(f"Right: {bounds.right:.6f}")
    print(f"Top: {bounds.top:.6f}")
    
    print("\n=== Additional Metadata ===")
    print(f"Width: {metadata['width']}")
    print(f"Height: {metadata['height']}")
    print(f"CRS: {metadata['crs']}")
    print(f"Transform: {metadata['transform']}")
    print(f"NoData value: {metadata['nodata']}")
    print(f"Data type: {metadata['dtype']}")

if __name__ == "__main__":
    # Example usage
    tif_path = rf"/mnt/c/Users/foo/Desktop/1x1_tif_outputs/10_DEM_y20x-110/xmin-106.000417_xmax-105.000417_ymin20.999583_ymax21.999583.tif"  # Replace with your .tif file path
    
    # Get bounds and metadata
    bounds, metadata = get_bounds_from_tif(tif_path)
    
    # Print the information
    print_bounds_info(bounds, metadata)
    