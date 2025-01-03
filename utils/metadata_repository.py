import boto3
from datetime import datetime

from configparser import ConfigParser
config = ConfigParser()
config.read('config.ini')

session = boto3.Session(
    aws_access_key_id=config['AWS']['ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS']['SECRET_ACCESS_KEY'],
    region_name='ap-southeast-2'
)

s3 = session.client('s3')

BUCKET = 'fta-mobile-observations-holding-bucket'
PREFIX = 'metadata'

def put_object(key, data):
    return s3.put_object(Bucket=BUCKET, Key=f"{PREFIX}/{key}", Body=data)

def get_object(key):
    response = s3.get_object(Bucket=BUCKET, Key=f"{PREFIX}/{key}")
    return response['Body'].read()

def update_object(key, data):
    return s3.put_object(Bucket=BUCKET, Key=f"{PREFIX}/{key}", Body=data)

def delete_object(key):
    now = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    copy_source = f"{PREFIX}/{key}"
    key_without_extension, extension = key.rsplit('.', 1)
    recycle_bin_key = f"recycle-bin/{PREFIX}/{key_without_extension}_{now}.{extension}"
    s3.copy_object(
        CopySource={'Bucket': BUCKET, 'Key': copy_source},
        Bucket=BUCKET,
        Key=recycle_bin_key
    )
    return s3.delete_object(Bucket=BUCKET, Key=copy_source)

def list_objects(key='', include_prefix=False):
    prefix = f"{PREFIX}/{key}" if key else PREFIX
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    raw_keys = [item['Key'] for item in response.get('Contents', [])]
    if include_prefix:
        return raw_keys
    return [key.split(f"{PREFIX}/")[1] for key in raw_keys]

def head_object(key):
    response = s3.head_object(Bucket=BUCKET, Key=f"{PREFIX}/{key}")
    return response['Metadata']