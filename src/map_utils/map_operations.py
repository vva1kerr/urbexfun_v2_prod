import folium
import geocoder
from typing import Tuple, Optional, Dict, Any
from src.get_coords.point_to_bounds import get_bounds_from_point
from src.get_coords.calculate_zoom import calculate_zoom_level

def create_map(
    lat: float,
    lon: float,
    zoom: int,
) -> folium.Map:
    """Create a folium map with the given parameters"""
    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom
    )
    
    # Add markers and other map elements here
    # if city and state:
    #     folium.Marker(
    #         [lat, lon],
    #         popup=f"{city}, {state}",
    #         tooltip=f"{city}, {state}"
    #     ).add_to(m)
    
    # if bounds:
    #     folium.Rectangle(
    #         bounds=[[bounds['min_lat'], bounds['min_lon']], 
    #                [bounds['max_lat'], bounds['max_lon']]],
    #         color="red",
    #         fill=True,
    #         fill_color="red",
    #         fill_opacity=0.2
    #     ).add_to(m)
    
    return m

def get_location_from_ip() -> Tuple[float, float]:
    """Get the current location based on IP address"""
    g = geocoder.ip('me')
    if not g.ok:
        raise ValueError("Could not get location from IP")
    return g.lat, g.lng

def get_location_from_city(city: str, state: str) -> Tuple[float, float]:
    """Get coordinates for a given city and state"""
    location = geocoder.osm(
        f"{city}, {state}, USA",
        headers={'User-Agent': 'urbexfun/1.0'},
        timeout=10
    )
    if not location.ok:
        raise ValueError(f"Could not find coordinates for {city}, {state}")
    return location.lat, location.lng

def get_map_parameters(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    use_ip_location: bool = True,
    city_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Get all necessary parameters for map creation"""
    try:
        if use_ip_location:
            lat, lon = lat, lon
        elif city and state and (use_ip_location == False):
            lat, lon = get_location_from_city(city, state)
        else:
            raise ValueError("Either use_ip_location must be True or city and state must be provided")
        
        if lat is None or lon is None:
            raise ValueError("Could not determine coordinates")
        
        # Get area from city_info if available, otherwise use a default value
        area_sq_miles = city_info.get('area_mile2', 100) if city_info else 100
        
        # Calculate bounds
        bounds = get_bounds_from_point(lat, lon, area_sq_miles)
        if not bounds:
            raise ValueError("Could not calculate bounds")
            
        # Calculate zoom level
        zoom = calculate_zoom_level(bounds)
        if zoom is None:
            zoom = 10  # Default zoom level if calculation fails
        
        return {
            'lat': lat,
            'lon': lon,
            'zoom': zoom,
            'bounds': bounds
        }
    except Exception as e:
        raise ValueError(f"Error getting map parameters: {str(e)}") 