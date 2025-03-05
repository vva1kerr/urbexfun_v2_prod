import os
from enum import Enum
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

from .base import BaseDataSource
from .local import LocalDataSource
from .mounted_s3 import MountedS3DataSource
from .boto3_s3 import Boto3S3DataSource

class DataSourceType(Enum):
    LOCAL = "local"
    MOUNTED_S3 = "mounted_s3"
    BOTO3 = "boto3"

class DataSourceFactory:
    """Factory class for creating data sources."""
    
    @staticmethod
    def create(
        source_type: DataSourceType,
        base_path: Optional[str] = None,
        bucket_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: Optional[str] = None,
        mount_point: Optional[str] = None
    ) -> BaseDataSource:
        """
        Create a data source instance based on the specified type.
        
        Args:
            source_type: Type of data source to create
            base_path: Base path for local files
            bucket_name: S3 bucket name (for boto3)
            aws_access_key_id: AWS access key ID (optional)
            aws_secret_access_key: AWS secret access key (optional)
            region_name: AWS region name (optional)
            mount_point: Path where S3 bucket is mounted (for mounted_s3)
            
        Returns:
            Configured data source instance
        """
        # Load environment variables if not provided
        if not aws_access_key_id:
            aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        if not aws_secret_access_key:
            aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        if not region_name:
            region_name = os.getenv('AWS_REGION_NAME')
        if not bucket_name:
            bucket_name = os.getenv('AWS_BUCKET_NAME')
        if not mount_point:
            mount_point = os.getenv('MOUNT_POINT')
        
        if source_type == DataSourceType.LOCAL:
            if not base_path:
                raise ValueError("base_path is required for LOCAL source type")
            return LocalDataSource(base_path)
            
        elif source_type == DataSourceType.MOUNTED_S3:
            if not mount_point:
                raise ValueError("mount_point is required for MOUNTED_S3 source type")
            return MountedS3DataSource(mount_point)
            
        else:  # BOTO3
            if not bucket_name:
                raise ValueError("bucket_name is required for BOTO3 source type")
            return Boto3S3DataSource(
                bucket_name=bucket_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name
            )

# Example usage:
"""
from src.data_sources.factory import DataSourceFactory, DataSourceType

# Create a local data source
local_source = DataSourceFactory.create(
    source_type=DataSourceType.LOCAL,
    base_path=rf"<filepath>"
)

# Create a mounted S3 data source
mounted_source = DataSourceFactory.create(
    source_type=DataSourceType.MOUNTED_S3
)  # Uses MOUNT_POINT from .env

# Create a boto3 S3 data source
s3_source = DataSourceFactory.create(
    source_type=DataSourceType.BOTO3
)  # Uses AWS credentials from .env
""" 