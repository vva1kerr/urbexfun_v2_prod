from pathlib import Path
from typing import Union, List, Tuple
from .base import BaseDataSource

class LocalDataSource(BaseDataSource):
    """Handles local file system data source."""
    
    def __init__(self, base_path: Union[str, Path]):
        """
        Initialize local data source.
        
        Args:
            base_path: Base directory path for local files
        """
        self.base_path = Path(base_path)
    
    def get_file_path(self, file_path: Union[str, Path]) -> Path:
        return self.base_path / file_path
    
    def read_file(self, file_path: Union[str, Path]) -> bytes:
        return (self.base_path / file_path).read_bytes()
    
    def list_files(self, prefix: str = "") -> List[str]:
        return [str(p) for p in (self.base_path / prefix).glob("**/*")]
        
    def get_tiff_path(self, lat: float, lon: float) -> Tuple[Path, float]:
        """
        Get the path to the TIFF file for the given coordinates and calculate downsampling factor.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Tuple of (TIFF file path, downsampling factor)
        """
        # For local files, we'll use a simple naming convention
        # Format: tile_{lat}_{lon}.tif
        tiff_name = f"tile_{lat:.2f}_{lon:.2f}.tif"
        tiff_path = self.get_file_path(tiff_name)
        
        # For local files, we'll use a default downsampling factor of 1
        # This can be adjusted based on file size if needed
        downsample_factor = 1.0
        
        return tiff_path, downsample_factor 