import boto3

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