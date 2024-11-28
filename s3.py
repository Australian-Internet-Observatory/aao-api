import boto3
import os
import json

from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

session_sydney = boto3.Session(
    region_name='ap-southeast-2',
    aws_access_key_id=config['AWS']['ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS']['SECRET_ACCESS_KEY']
)

MOBILE_OBSERVATIONS_BUCKET = 'fta-mobile-observations-v2'

client = session_sydney.client('s3')

def list_dir(path=""):
    # If the path does not have an extension, it is a directory
    if not os.path.splitext(path)[1] and not path.endswith('/'):
        path += '/'
    # for obj in observation_bucket.objects.filter(Prefix=path, Delimiter='/'):
    #     print(obj.key)
    kwargs = {
        'Bucket': MOBILE_OBSERVATIONS_BUCKET, 
        'Delimiter': '/'
    }
    if path and path not in ["/", "", ".", "./"]:
        kwargs['Prefix'] = path
    client_response = client.list_objects_v2(**kwargs)
    dir_elements = []
    for content in client_response.get('CommonPrefixes', []):
        dir_name = content.get('Prefix')
        dir_elements.append(dir_name)
    for content in client_response.get('Contents', []):
        file_name = content.get('Key')
        dir_elements.append(file_name)
    return dir_elements

def read_json_file(path):
    try:
        obj = client.get_object(Bucket=MOBILE_OBSERVATIONS_BUCKET, Key=path)
        data = obj['Body'].read().decode('utf-8')
        return json.loads(data)
    except Exception as e:
        return None
    
def try_get_object(key, bucket=MOBILE_OBSERVATIONS_BUCKET):
    try:
        return client.get_object(Bucket=bucket, Key=key)
    except Exception as e:
        return None