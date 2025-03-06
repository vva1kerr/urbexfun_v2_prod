import math
from dataclasses import dataclass
from typing import Tuple
import rasterio
from rasterio.merge import merge
from rasterio.mask import mask
from pathlib import Path
import os
from typing import List
import math
from shapely.geometry import box
import numpy as np
from src.config.data_source_config import get_data_source

@dataclass
class Bounds:
    """Class to hold boundary coordinates"""
    left: float
    bottom: float
    right: float
    top: float

def calculate_zoom_bounds(lat: float, lon: float, elevation_meters: float) -> Bounds:
    """
    Calculate the bounds for a given point based on elevation.
    The higher the elevation, the larger the area covered.
    
    Args:
        lat (float): Latitude in decimal degrees
        lon (float): Longitude in decimal degrees
        elevation_meters (float): Elevation in meters
        
    Returns:
        Bounds: Object containing the calculated bounds
    """
    # Earth's radius in meters
    EARTH_RADIUS = 6371000
    
    # Convert elevation to degrees (approximate)
    # This is a simplified calculation - the actual relationship between
    # elevation and visible area is more complex due to Earth's curvature
    # and terrain variations
    elevation_degrees = elevation_meters / 1000  # Rough approximation
    
    # Calculate the bounds
    # For each degree of elevation, we'll cover approximately that many degrees
    # of latitude and longitude
    lat_span = elevation_degrees
    lon_span = elevation_degrees * math.cos(math.radians(lat))  # Adjust for latitude
    
    # Calculate the bounds
    left = lon - (lon_span / 2)
    right = lon + (lon_span / 2)
    bottom = lat - (lat_span / 2)
    top = lat + (lat_span / 2)
    
    return Bounds(left=left, bottom=bottom, right=right, top=top)


def get_required_file_names(bounds: Bounds) -> list[str]:
    """
    Determine the required TIFF file names based on the given bounds.
    
    Args:
        bounds (Bounds): The calculated bounds from calculate_zoom_bounds
        
    Returns:
        list[str]: List of required TIFF file names
    """
    # Round bounds to nearest integer for file naming
    x_min = math.floor(bounds.left)
    x_max = math.ceil(bounds.right)
    y_min = math.floor(bounds.bottom)
    y_max = math.ceil(bounds.top)
    
    required_files = []
    
    # Generate all possible combinations of files needed
    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            # Format: xmin-86_xmax-85_ymin34_ymax35.tif
            filename = f"xmin{x}_xmax{x+1}_ymin{y}_ymax{y+1}.tif"
            required_files.append(filename)
    
    return required_files
















def round_coordinate_for_filename(coord: float) -> int:
    """
    Round coordinate to nearest integer for filename.
    For example:
    - 60.999 rounds to 61
    - 60.00001 rounds to 60
    - -60.9999 rounds to -61
    - -60.00001 rounds to -60
    """
    return round(coord)

def save_combined_tiff(merged_data, merged_transform, meta, output_path: str) -> bool:
    """
    Save the combined TIFF data to a file.
    
    Args:
        merged_data: The combined data array
        merged_transform: The transform for the merged data
        meta: The metadata dictionary
        output_path: Path where to save the file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Update metadata with merged dimensions and transform
        meta.update({
            'height': merged_data.shape[1],
            'width': merged_data.shape[2],
            'transform': merged_transform
        })
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write the merged data to a new file
        with rasterio.open(output_path, 'w', **meta) as dst:
            dst.write(merged_data)
            
        return True
    except Exception as e:
        print(f"Error saving combined TIFF: {str(e)}")
        return False

def crop_tiff(input_path: str, bounds, output_path: str) -> bool:
    """
    Crop a TIFF file to the specified bounds.
    
    Args:
        input_path: Path to the input TIFF file
        bounds: The bounds to crop to
        output_path: Path where to save the cropped file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create a bounding box for cropping
        bbox = box(bounds.left, bounds.bottom, bounds.right, bounds.top)
        
        # Open the input file and crop it
        with rasterio.open(input_path) as src:
            # Crop the data to the bounds
            cropped_data, cropped_transform = mask(
                src,
                [bbox],
                crop=True,
                all_touched=True
            )
            
            # Get metadata and update it
            meta = src.meta.copy()
            meta.update({
                'height': cropped_data.shape[1],
                'width': cropped_data.shape[2],
                'transform': cropped_transform
            })
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write the cropped data to the output file
            with rasterio.open(output_path, 'w', **meta) as dst:
                dst.write(cropped_data)
                
        return True
    except Exception as e:
        print(f"Error cropping TIFF: {str(e)}")
        return False


def combine_tiff_files(input_dir: str, output_path: str, lat: float, lon: float, elevation: float, crop_to_bounds: bool = True) -> bool:
    """
    Combine multiple TIFF files into a single TIFF file based on bounds calculated from a point.
    
    Args:
        input_dir (str): Directory containing the input TIFF files
        output_path (str): Path where the combined TIFF will be saved
        lat (float): Latitude of the center point
        lon (float): Longitude of the center point
        elevation (float): Elevation in meters
        crop_to_bounds (bool): Whether to crop the output to the calculated bounds
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Calculate bounds and get required file names
        bounds = calculate_zoom_bounds(lat, lon, elevation)
        print(f"Calculated bounds: {bounds}")
        required_files = get_required_file_names(bounds)
        print(f"Required files: {required_files}")
        
        # Convert input directory to Path object and expand user path
        input_path = Path(input_dir)
        print(f"Input directory (before expansion): {input_dir}")
        print(f"Input directory (after Path conversion): {input_path}")
        print(f"Input directory exists: {input_path.exists()}")
        
        # Find all matching files in the input directory
        tiff_files = []
        for file in required_files:
            # Search for the file in the input directory
            file_path = input_path / file
            if file_path.exists():
                tiff_files.append(str(file_path))
                print(f"Found file: {file_path}")
            else:
                print(f"Warning: Could not find file {file}")
                # List contents of directory to help debug
                print(f"Directory contents: {list(input_path.glob('*.tif'))}")
        
        if not tiff_files:
            print("Error: No matching TIFF files found")
            return False
            
        print(f"\nFound {len(tiff_files)} files to combine")
        
        # Open all TIFF files
        src_files = [rasterio.open(f) for f in tiff_files]
        
        # Merge the datasets
        merged_data, merged_transform = merge(src_files)
        
        # Get metadata from the first source
        meta = src_files[0].meta.copy()
        
        # Close all source files
        for src in src_files:
            src.close()
        
        # Create paths for temporary and final files
        base_path = output_path.replace('.tif', '')
        temp_path = f"{base_path}_temp.tif"
        
        # First save the full combined file to temp
        if not save_combined_tiff(merged_data, merged_transform, meta, temp_path):
            return False
            
        # If we want the cropped version
        if crop_to_bounds:
            if not crop_tiff(temp_path, bounds, output_path):
                # Clean up temp file if cropping fails
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return False
            # Remove the temp file since we only want the adjusted version
            if os.path.exists(temp_path):
                os.remove(temp_path)
        else:
            # If we don't want cropping, rename temp to final output
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(temp_path, output_path)
            
        print(f"\nSuccessfully combined {len(tiff_files)} TIFF files into: {output_path}")
        print(f"Output bounds: {bounds}")
        return True
        
    except Exception as e:
        print(f"Error combining TIFF files: {str(e)}")
        # Clean up any temporary files
        if os.path.exists(output_path + '.temp'):
            os.remove(output_path + '.temp')
        return False