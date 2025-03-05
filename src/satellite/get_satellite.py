import cv2
import requests
import numpy as np
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time


def project_with_scale(lat, lon, scale):
    """Mercator projection with scale"""
    siny = np.sin(lat * np.pi / 180)
    siny = min(max(siny, -0.9999), 0.9999)
    x = scale * (0.5 + lon / 360)
    y = scale * (0.5 - np.log((1 + siny) / (1 - siny)) / (4 * np.pi))
    return x, y

def create_session_with_retries():
    """Create a requests session with retry strategy"""
    session = requests.Session()
    retries = Retry(
        total=5,  # number of retries
        backoff_factor=0.1,  # time factor between retries
        status_forcelist=[500, 502, 503, 504],  # HTTP status codes to retry on
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

def download_tile(url, headers, channels):
    """Download a single map tile with retries"""
    session = create_session_with_retries()
    max_attempts = 2
    
    for attempt in range(max_attempts):
        try:
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise an error for bad status codes
            arr = np.asarray(bytearray(response.content), dtype=np.uint8)
            return cv2.imdecode(arr, 1) if channels == 3 else cv2.imdecode(arr, -1)
        except Exception as e:
            if attempt == max_attempts - 1:  # Last attempt
                return None
            time.sleep(1)  # Wait before retrying

def get_satellite_image(lat1, lon1, lat2, lon2, zoom=12, progress_callback=None): 
    """Get satellite imagery for the specified bounds"""
    
    # Ensure correct coordinate ordering
    min_lat, max_lat = min(lat1, lat2), max(lat1, lat2)
    min_lon, max_lon = min(lon1, lon2), max(lon1, lon2)
    
    # Configuration
    tile_size = 256
    channels = 3
    url = 'https://mt.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36'
    }
    
    scale = 1 << zoom
    
    # Find pixel and tile coordinates
    tl_proj_x, tl_proj_y = project_with_scale(max_lat, min_lon, scale)  # Top-left uses max_lat
    br_proj_x, br_proj_y = project_with_scale(min_lat, max_lon, scale)  # Bottom-right uses min_lat
    
    tl_pixel_x = int(tl_proj_x * tile_size)
    tl_pixel_y = int(tl_proj_y * tile_size)
    br_pixel_x = int(br_proj_x * tile_size)
    br_pixel_y = int(br_proj_y * tile_size)
    
    tl_tile_x = int(tl_proj_x)
    tl_tile_y = int(tl_proj_y)
    br_tile_x = int(br_proj_x)
    br_tile_y = int(br_proj_y)
    
    # Create image array
    img_w = abs(tl_pixel_x - br_pixel_x)
    img_h = br_pixel_y - tl_pixel_y
    img = np.zeros((img_h, img_w, channels), np.uint8)
    
    # Calculate total tiles for progress tracking
    total_tiles = (br_tile_x - tl_tile_x + 1) * (br_tile_y - tl_tile_y + 1)
    tiles_processed = 0
    
    # Download and stitch tiles
    for tile_y in range(tl_tile_y, br_tile_y + 1):
        for tile_x in range(tl_tile_x, br_tile_x + 1):
            tile = download_tile(url.format(x=tile_x, y=tile_y, z=zoom), headers, channels)
            
            if tile is not None:
                # Calculate tile placement
                tl_rel_x = tile_x * tile_size - tl_pixel_x
                tl_rel_y = tile_y * tile_size - tl_pixel_y
                br_rel_x = tl_rel_x + tile_size
                br_rel_y = tl_rel_y + tile_size
                
                # Define placement bounds
                img_x_l = max(0, tl_rel_x)
                img_x_r = min(img_w + 1, br_rel_x)
                img_y_l = max(0, tl_rel_y)
                img_y_r = min(img_h + 1, br_rel_y)
                
                # Define crop bounds
                cr_x_l = max(0, -tl_rel_x)
                cr_x_r = tile_size + min(0, img_w - br_rel_x)
                cr_y_l = max(0, -tl_rel_y)
                cr_y_r = tile_size + min(0, img_h - br_rel_y)
                
                # Place tile in image
                img[img_y_l:img_y_r, img_x_l:img_x_r] = tile[cr_y_l:cr_y_r, cr_x_l:cr_x_r]
            
            # Update progress
            tiles_processed += 1
            if progress_callback:
                progress_callback(tiles_processed / total_tiles)
    
    return img