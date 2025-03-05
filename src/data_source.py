import os
import boto3
from enum import Enum
from typing import Union, Optional
from pathlib import Path

class DataSourceType(Enum):
    LOCAL = "local"
    MOUNTED_S3 = "mounted_s3"
    BOTO3 = "boto3"

class DataSource:
    def __init__(
        self,
        source_type: DataSourceType,
        base_path: str,
        bucket_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: Optional[str] = None
    ):
        """
        Initialize the data source handler.
        
        Args:
            source_type: Type of data source (LOCAL, MOUNTED_S3, or BOTO3)
            base_path: Base path for local or mounted S3 files
            bucket_name: S3 bucket name (required for BOTO3)
            aws_access_key_id: AWS access key ID (optional for BOTO3)
            aws_secret_access_key: AWS secret access key (optional for BOTO3)
            region_name: AWS region name (optional for BOTO3)
        """
        self.source_type = source_type
        self.base_path = Path(base_path)
        
        if source_type == DataSourceType.BOTO3:
            if not bucket_name:
                raise ValueError("bucket_name is required for BOTO3 source type")
            
            # Initialize S3 client
            session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name
            )
            self.s3_client = session.client('s3')
            self.bucket_name = bucket_name

    def get_file_path(self, file_path: Union[str, Path]) -> Path:
        """
        Get the full file path based on the source type.
        
        Args:
            file_path: Relative file path
            
        Returns:
            Full file path
        """
        file_path = Path(file_path)
        
        if self.source_type in [DataSourceType.LOCAL, DataSourceType.MOUNTED_S3]:
            return self.base_path / file_path
        else:
            return file_path

    def read_file(self, file_path: Union[str, Path]) -> bytes:
        """
        Read file content based on the source type.
        
        Args:
            file_path: Relative file path
            
        Returns:
            File content as bytes
        """
        file_path = Path(file_path)
        
        if self.source_type == DataSourceType.LOCAL:
            return (self.base_path / file_path).read_bytes()
        elif self.source_type == DataSourceType.MOUNTED_S3:
            return (self.base_path / file_path).read_bytes()
        else:  # BOTO3
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=str(file_path)
            )
            return response['Body'].read()

    def list_files(self, prefix: str = "") -> list:
        """
        List files in the data source.
        
        Args:
            prefix: Prefix to filter files (for S3) or subdirectory (for local/mounted)
            
        Returns:
            List of file paths
        """
        if self.source_type == DataSourceType.LOCAL:
            return [str(p) for p in (self.base_path / prefix).glob("**/*")]
        elif self.source_type == DataSourceType.MOUNTED_S3:
            return [str(p) for p in (self.base_path / prefix).glob("**/*")]
        else:  # BOTO3
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            return [obj['Key'] for obj in response.get('Contents', [])]

# Example usage:
"""
# For local files
local_source = DataSource(
    source_type=DataSourceType.LOCAL,
    base_path="/path/to/local/data"
)

# For mounted S3 bucket
mounted_source = DataSource(
    source_type=DataSourceType.MOUNTED_S3,
    base_path="/mnt/s3bucket"
)

# For boto3 S3 client
s3_source = DataSource(
    source_type=DataSourceType.BOTO3,
    base_path="",  # Not used for boto3
    bucket_name="my-bucket",
    aws_access_key_id="your-access-key",  # Optional if using AWS credentials file
    aws_secret_access_key="your-secret-key",  # Optional if using AWS credentials file
    region_name="us-east-1"  # Optional
)
""" 