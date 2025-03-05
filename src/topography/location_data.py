from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class LocationData:
    """Data class to store location information including center point and bounds."""
    
    data: Dict[str, Any]
    
    def __post_init__(self):
        """Initialize or update the data structure."""
        if not isinstance(self.data, dict):
            raise ValueError("data must be a dictionary")
            
        # Ensure all required keys exist
        if 'center_point' not in self.data:
            self.data['center_point'] = {}
        if 'bounds' not in self.data:
            self.data['bounds'] = {}
            
        # Calculate bounds if not provided
        if not all(key in self.data['bounds'] for key in ['min_lat', 'max_lat', 'min_lon', 'max_lon']):
            if 'scale' not in self.data:
                self.data['scale'] = 1.0  # default scale
                
            self.data['bounds'] = {
                'min_lon': self.data['center_point']['lon'] - self.data['scale']/2,
                'min_lat': self.data['center_point']['lat'] - self.data['scale']/2,
                'max_lon': self.data['center_point']['lon'] + self.data['scale']/2,
                'max_lat': self.data['center_point']['lat'] + self.data['scale']/2
            }
    
    @property
    def bounds_obj(self):
        """Create a bounds object for plotting."""
        return type('Bounds', (), {
            'left': self.data['bounds']['min_lon'],
            'right': self.data['bounds']['max_lon'],
            'bottom': self.data['bounds']['min_lat'],
            'top': self.data['bounds']['max_lat']
        })
    
    def format_coordinates(self) -> str:
        """Format coordinates nicely with N/S and E/W indicators."""
        lat = self.data['center_point']['lat']
        lon = self.data['center_point']['lon']
        lat_dir = "N" if lat >= 0 else "S"
        lon_dir = "E" if lon >= 0 else "W"
        return f"({abs(lat):.2f}°{lat_dir}, {abs(lon):.2f}°{lon_dir})"

# Example usage:
"""
# Create from center point and scale
location = LocationData({
    'center_point': {
        'lat': 40.73,
        'lon': -73.93
    },
    'scale': 1.0
})

# Or create with explicit bounds
location = LocationData({
    'center_point': {
        'lat': 40.73,
        'lon': -73.93
    },
    'bounds': {
        'min_lat': 40.23,
        'max_lat': 41.23,
        'min_lon': -74.43,
        'max_lon': -73.43
    }
})

# Use for plotting
fig_dem = create_dem_plot(data, location.bounds_obj, location.format_coordinates())
fig_ridge = create_ridge_plot_optimized(data, location.format_coordinates())
fig_3d = create_3d_plot(data, location.bounds_obj)
m = create_map(location.data['center_point']['lat'], location.data['center_point']['lon'], zoom=10)
""" 