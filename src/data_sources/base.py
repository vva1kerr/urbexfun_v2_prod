from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, List

class BaseDataSource(ABC):
    """Abstract base class for all data sources."""
    
    @abstractmethod
    def get_file_path(self, file_path: Union[str, Path]) -> Path:
        """Get the full file path."""
        pass
    
    @abstractmethod
    def read_file(self, file_path: Union[str, Path]) -> bytes:
        """Read file content."""
        pass
    
    @abstractmethod
    def list_files(self, prefix: str = "") -> List[str]:
        """List files in the data source."""
        pass 