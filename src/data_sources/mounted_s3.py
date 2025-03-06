from pathlib import Path
from typing import Union, List
from .base import BaseDataSource

class MountedS3DataSource(BaseDataSource):
    """Handles mounted S3 bucket data source."""
    
    def __init__(self, mount_point: Union[str, Path]):
        """
        Initialize mounted S3 data source.
        
        Args:
            mount_point: Path where the S3 bucket is mounted
        """
        # Expand user path and convert to Path object
        self.mount_point = Path(mount_point).expanduser()
        print(f"MountedS3DataSource initialized with mount point: {self.mount_point}")  # Debug print
    
    def get_file_path(self, file_path: Union[str, Path]) -> Path:
        return self.mount_point / file_path
    
    def read_file(self, file_path: Union[str, Path]) -> bytes:
        return (self.mount_point / file_path).read_bytes()
    
    def list_files(self, prefix: str = "") -> List[str]:
        return [str(p) for p in (self.mount_point / prefix).glob("**/*")] 