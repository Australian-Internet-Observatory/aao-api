from routes import route
from middlewares.authenticate import authenticate
from utils import use, jwt
import hashlib
import boto3
import time
import json

from configparser import ConfigParser
config = ConfigParser()
config.read('config.ini')

session = boto3.Session(
    aws_access_key_id=config['AWS']['ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS']['SECRET_ACCESS_KEY'],
    region_name='ap-southeast-2'
)

META_BUCKET = 'fta-mobile-observations-holding-bucket'
ADS_BUCKET = 'fta-mobile-observations-v2'
USERS_FOLDER_PREFIX = 'metadata/dashboard-users'
AD_ATTRIBUTES_PREFIX = 'metadata/ad-custom-attributes'

@route('ads/attributes', 'POST')
@use(authenticate)
def get_properties(event):
    """Retrieve ad attributes from the S3 bucket.

    Retrieve custom attributes for the specified ads from the S3 bucket.
    ---
    tags:
        - ads
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        ads:
                            type: array
                            items:
                                type: object
                                properties:
                                    ad_id:
                                        type: string
                                    observer:
                                        type: string
                                    timestamp:
                                        type: integer
    responses:
        200:
            description: A successful response
            content:
                application/json:
                    schema:
                        type: array
                        items:
                            type: object
        400:
            description: A failed response
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                            comment:
                                type: string
    """
    ads = event['body']['ads']
    # Each ad should be an object with an 'ad_id' key
    s3 = session.client('s3')
    ad_attributes = []
    for ad in ads:
        observer_id = ad['observer']
        timestamp = ad['timestamp']
        ad_id = ad['ad_id']
        ad_attributes_path = f'{AD_ATTRIBUTES_PREFIX}/{observer_id}_{timestamp}.{ad_id}.json'
        try:
            ad_attributes_object = s3.get_object(
                Bucket=META_BUCKET,
                Key=ad_attributes_path
            )
            ad_attributes_data = json.loads(ad_attributes_object['Body'].read().decode('utf-8'))
            ad_attributes.append({
                **ad,
                'attributes': ad_attributes_data
            })
        except Exception as e:
            ad_attributes.append([])
    return ad_attributes
    
@route('ads/attributes/add', 'POST')
@use(authenticate)
def add_properties(event):
    """Add or update ad attributes in the S3 bucket.

    Add or update custom attributes for the specified ad in the S3 bucket.
    ---
    tags:
        - ads
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        ad:
                            type: object
                            properties:
                                ad_id:
                                    type: string
                                observer:
                                    type: string
                                timestamp:
                                    type: integer
                        attribute:
                            type: object
                            properties:
                                key:
                                    type: string
                                value:
                                    type: string
    responses:
        200:
            description: A successful response
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                            comment:
                                type: string
        400:
            description: A failed response
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                            comment:
                                type: string
    """
    ad_data = event['body']['ad']
    observer_id = ad_data['observer']
    timestamp = ad_data['timestamp']
    ad_id = ad_data['ad_id']
    attribute = event['body']['attribute']
    # Ensure the ad actually exists in the S3 bucket
    ad_path = f'{observer_id}/temp/{timestamp}.{ad_id}/'
    print('AD PATH:', ad_path)
    s3 = session.client('s3')
    try:
        # Ensure the folder exists
        s3.list_objects_v2(Bucket=ADS_BUCKET, Prefix=ad_path)
    except Exception as e:
        return {
            "success": False,
            "comment": "AD_NOT_FOUND"
        }
    # Add the tag to the ad with the given ad_id
    ad_attributes_path = f'{AD_ATTRIBUTES_PREFIX}/{observer_id}_{timestamp}.{ad_id}.json'
    print('AD ATTRIBUTES PATH:', ad_attributes_path)
    # Create the ad attributes file if it doesn't exist
    try:
        s3.head_object(Bucket=META_BUCKET, Key=ad_attributes_path)
    except Exception as e:
        print('Creating new ad attributes file...')
        s3.put_object(
            Bucket=META_BUCKET,
            Key=ad_attributes_path,
            Body=b'{}'
        )
    # Load the ad attributes file
    ad_attributes_object = s3.get_object(
        Bucket=META_BUCKET,
        Key=ad_attributes_path
    )
    ad_attributes_data = json.loads(ad_attributes_object['Body'].read().decode('utf-8'))
    print('AD ATTRIBUTES DATA:', ad_attributes_data)
    # If the object already exist, overwrite it and update the modified_at and modified_by fields
    key = attribute['key']
    if key in ad_attributes_data:
        ad_attributes_data[key]['value'] = attribute['value']
        ad_attributes_data[key]['modified_at'] = int(time.time())
        ad_attributes_data[key]['modified_by'] = event['user']['username']
    # Otherwise, create a new object with the modified_at and modified_by fields
    else:
        ad_attributes_data[key] = {
            'value': attribute['value'],
            'created_at': int(time.time()),
            'created_by': event['user']['username'],
            'modified_at': int(time.time()),
            'modified_by': event['user']['username'],
        }
    s3.put_object(
        Bucket=META_BUCKET,
        Key=ad_attributes_path,
        Body=json.dumps(ad_attributes_data).encode('utf-8')
    )