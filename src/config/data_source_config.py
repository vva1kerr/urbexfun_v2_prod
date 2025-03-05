import os
from dotenv import load_dotenv
from src.data_sources.factory import DataSourceFactory, DataSourceType

# Load environment variables
load_dotenv()

# Default paths and settings
DEFAULT_LOCAL_PATH = os.getenv(rf'LOCAL_DATA_PATH')
DEFAULT_MOUNT_POINT = os.getenv('MOUNT_POINT')
DEFAULT_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
DEFAULT_REGION = os.getenv('AWS_REGION_NAME')

# Create data source instances
def get_local_source():
    """Get local file system data source."""
    return DataSourceFactory.create(
        source_type=DataSourceType.LOCAL,
        base_path=DEFAULT_LOCAL_PATH
    )

def get_mounted_s3_source():
    """Get mounted S3 bucket data source."""
    return DataSourceFactory.create(
        source_type=DataSourceType.MOUNTED_S3,
        mount_point=DEFAULT_MOUNT_POINT
    )

def get_boto3_s3_source():
    """Get boto3 S3 client data source."""
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

# Default data source to use
DEFAULT_SOURCE = 'local'

def get_data_source(source_name: str = None) -> DataSourceFactory:
    """
    Get a data source instance by name.
    
    Args:
        source_name: Name of the data source to use. If None, uses DEFAULT_SOURCE.
        
    Returns:
        Configured data source instance
    """
    if source_name is None:
        source_name = DEFAULT_SOURCE
        
    if source_name not in DATA_SOURCES:
        raise ValueError(f"Unknown data source: {source_name}")
        
    return DATA_SOURCES[source_name]() 