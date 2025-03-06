import os
from dotenv import load_dotenv
from src.data_sources.factory import DataSourceFactory, DataSourceType
from typing import Optional, Union
from pathlib import Path

# Force reload environment variables
load_dotenv(override=True)

# Debug print all relevant environment variables
print("Environment variables:")
print(f"MOUNT_POINT: {os.getenv('MOUNT_POINT')}")
print(f"LOCAL_DATA_PATH: {os.getenv('LOCAL_DATA_PATH')}")
print(f"DEFAULT_DATA_SOURCE: {os.getenv('DEFAULT_DATA_SOURCE')}")

# Default paths and settings
DEFAULT_LOCAL_PATH = os.getenv('LOCAL_DATA_PATH')
DEFAULT_MOUNT_POINT = os.getenv('MOUNT_POINT', '~/s3bucket').strip("'").strip('"').rstrip('/')  # Clean up the path
print(f"Cleaned MOUNT_POINT: {DEFAULT_MOUNT_POINT}")  # Debug print
DEFAULT_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
DEFAULT_REGION = os.getenv('AWS_REGION_NAME')

# Default data source to use (configurable via environment variable)
DEFAULT_SOURCE = os.getenv('DEFAULT_DATA_SOURCE', 'mounted_s3').strip("'").strip('"').strip('/')  # Clean up the source name
print(f"Cleaned DEFAULT_SOURCE: {DEFAULT_SOURCE}")  # Debug print

# Create data source instances
def get_local_source():
    """Get local file system data source."""
    if not DEFAULT_LOCAL_PATH:
        raise ValueError("LOCAL_DATA_PATH environment variable is not set")
    base_path = Path(DEFAULT_LOCAL_PATH).expanduser()
    if not base_path.exists():
        raise ValueError(f"Local data path {base_path} does not exist")
    return DataSourceFactory.create(
        source_type=DataSourceType.LOCAL,
        base_path=str(base_path)
    )

def get_mounted_s3_source():
    """Get mounted S3 bucket data source."""
    # Get the mount point from .env and clean it
    mount_point = DEFAULT_MOUNT_POINT.strip("'").strip('"').rstrip('/')
    print(f"Mount point from .env: {mount_point}")  # Debug print
    
    # Handle path expansion based on user
    if os.geteuid() == 0:  # Running as root
        # Replace ~ with /home/ubuntu when running as root
        mount_point = mount_point.replace('~', '/home/ubuntu')
        print(f"Running as root, expanded path: {mount_point}")  # Debug print
    else:
        # Normal case - expand user path
        mount_point = str(Path(mount_point).expanduser())
        print(f"Normal case, expanded path: {mount_point}")  # Debug print
    
    mount_point_path = Path(mount_point)
    if not mount_point_path.exists():
        raise ValueError(f"Mount point {mount_point_path} does not exist. Please check your .env file and ensure the path is correct.")
    return DataSourceFactory.create(
        source_type=DataSourceType.MOUNTED_S3,
        mount_point=str(mount_point_path)
    )

def get_boto3_s3_source():
    """Get boto3 S3 client data source."""
    if not DEFAULT_BUCKET_NAME or not DEFAULT_REGION:
        raise ValueError("AWS_BUCKET_NAME and AWS_REGION_NAME environment variables must be set")
    return DataSourceFactory.create(
        source_type=DataSourceType.BOTO3,
        bucket_name=DEFAULT_BUCKET_NAME,
        region_name=DEFAULT_REGION
    )

# Dictionary mapping source names to their factory functions
DATA_SOURCES = {
    'local': get_local_source,
    'mounted_s3': get_mounted_s3_source,
    'boto3_s3': get_boto3_s3_source
}

def get_base_path(data_source) -> Path:
    """
    Get the base path from any data source type.
    
    Args:
        data_source: The data source instance
        
    Returns:
        Path object representing the base path
    """
    print(f"Getting base path from data source type: {type(data_source).__name__}")  # Debug print
    if hasattr(data_source, 'mount_point'):
        path = Path(data_source.mount_point)
        print(f"Using mount_point: {path}")  # Debug print
        return path
    elif hasattr(data_source, 'base_path'):
        path = Path(data_source.base_path)
        print(f"Using base_path: {path}")  # Debug print
        return path
    else:
        raise AttributeError("Data source must have either mount_point or base_path attribute")

def get_data_source(source_name: Optional[str] = None) -> DataSourceFactory:
    """
    Get a data source instance by name.
    
    Args:
        source_name: Name of the data source to use. If None, uses DEFAULT_SOURCE.
        
    Returns:
        Configured data source instance
    """
    if source_name is None:
        source_name = DEFAULT_SOURCE
        print(f"Using default source: {source_name}")  # Debug print
        
    if source_name not in DATA_SOURCES:
        raise ValueError(f"Unknown data source: {source_name}. Available sources: {', '.join(DATA_SOURCES.keys())}")
        
    print(f"Creating data source: {source_name}")  # Debug print
    return DATA_SOURCES[source_name]() 