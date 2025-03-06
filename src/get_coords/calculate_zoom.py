import math
import streamlit as st
def calculate_zoom_level(bounds):
    """
    Calculate the appropriate zoom level to fit the given bounds.
    
    Args:
        bounds (dict): Dictionary containing min_lat, max_lat, min_lon, max_lon coordinates
        
    Returns:
        int: Zoom level (0-18, where 0 is most zoomed out)
    """
    # Get the bounds

    north = bounds['bounds']['max_lat']
    south = bounds['bounds']['min_lat']
    east = bounds['bounds']['max_lon']
    west = bounds['bounds']['min_lon']
    
    # Calculate the angular distance
    lat_diff = abs(north - south)
    lon_diff = abs(east - west)
    
    # Use the larger difference to determine zoom level
    max_diff = max(lat_diff, lon_diff)
    
    # Calculate zoom level (logarithmic scale)
    # Base zoom level on the maximum difference
    zoom = int(round(math.log(360 / max_diff) / math.log(2)))
    
    # Clamp zoom level between 0 and 18
    return max(0, min(18, zoom)) 