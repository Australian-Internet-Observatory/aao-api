import json
import boto3
from botocore.exceptions import ClientError
from db.clients.base_storage_client import BaseStorageClient

from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

class S3StorageClient(BaseStorageClient):
    """A client for Amazon S3 storage."""
    def __init__(self, **config: dict):
        """Initialize the S3 storage client with configuration parameters.

        Args:
            config (dict): Configuration parameters for the S3 client.
        """
        super().__init__(**config)
        self.s3 = None
        self.bucket = config.get('bucket')
        if not self.bucket:
            raise ValueError("Bucket name must be provided in the configuration.")
        # The subdirectory in the S3 bucket where objects are stored,
        # should not end with a slash
        self.prefix = config.get('prefix', '')
        if self.prefix.endswith('/'):
            self.prefix = self.prefix[:-1]
        # The file extension for the objects stored in S3
        self.extension = config.get('extension', 'json')

    def connect(self):
        """Connect to the S3 service."""
        session = boto3.Session(
            aws_access_key_id=config['AWS']['ACCESS_KEY_ID'],
            aws_secret_access_key=config['AWS']['SECRET_ACCESS_KEY'],
            region_name='ap-southeast-2'
        )
        self.s3 = session.client('s3')
        self.connected = True

    def disconnect(self):
        """Disconnect from the S3 service."""
        self.s3 = None
        self.connected = False

    def get(self, key: str):
        """Retrieve an object from the S3 bucket."""
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=f"{self.prefix}/{key}.{self.extension}")
            body = response['Body'].read().decode('utf-8')
            return json.loads(body)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise

    def put(self, key: str, value):
        """Store an object in the S3 bucket."""
        self.s3.put_object(Bucket=self.bucket, Key=f"{self.prefix}/{key}.{self.extension}", Body=json.dumps(value))

    def delete(self, key: str):
        """Delete an object from the S3 bucket."""
        self.s3.delete_object(Bucket=self.bucket, Key=f"{self.prefix}/{key}.{self.extension}")

    def list_ids(self):
        """List all object IDs in the S3 bucket."""
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=self.prefix)
            return [
                obj['Key'].split('/')[-1].replace(f'.{self.extension}', '')
                for obj in response.get('Contents', [])
            ]
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                return []
            raise

    def list(self):
        """List all objects in the S3 bucket."""
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=self.prefix)
            return [
                {
                    'key': obj['Key'].split('/')[-1].replace(f'.{self.extension}', ''),
                    'value': json.loads(self.s3.get_object(Bucket=self.bucket, Key=obj['Key'])['Body'].read().decode('utf-8'))
                }
                for obj in response.get('Contents', [])
            ]
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                return []
            raise