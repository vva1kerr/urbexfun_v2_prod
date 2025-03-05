import boto3
from pathlib import Path
from typing import Union, List, Optional
from .base import BaseDataSource

class Boto3S3DataSource(BaseDataSource):
    """Handles S3 data source using boto3."""
    
    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: Optional[str] = None
    ):
        """
        Initialize boto3 S3 data source.
        
        Args:
            bucket_name: Name of the S3 bucket
            aws_access_key_id: AWS access key ID (optional)
            aws_secret_access_key: AWS secret access key (optional)
            region_name: AWS region name (optional)
        """
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        self.s3_client = session.client('s3')
        self.bucket_name = bucket_name
    
    def get_file_path(self, file_path: Union[str, Path]) -> Path:
        return Path(file_path)
    
    def read_file(self, file_path: Union[str, Path]) -> bytes:
        response = self.s3_client.get_object(
            Bucket=self.bucket_name,
            Key=str(file_path)
        )
        return response['Body'].read()
    
    def list_files(self, prefix: str = "") -> List[str]:
        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix
        )
        return [obj['Key'] for obj in response.get('Contents', [])] 