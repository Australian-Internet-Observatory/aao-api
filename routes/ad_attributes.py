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

@route('ads/{observer_id}/{timestamp}.{ad_id}/attributes', 'GET')
@use(authenticate)
def get_attributes(event, response):
    """Retrieve all attributes for an ad.

    Retrieve all custom attributes for the specified ad.
    ---
    tags:
        - ads/attributes
    parameters:
        - in: path
          name: observer_id
          required: true
          schema:
              type: string
        - in: path
          name: timestamp
          required: true
          schema:
              type: string
        - in: path
          name: ad_id
          required: true
          schema:
              type: string
    responses:
        200:
            description: A successful response
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            ad_id:
                                type: string
                            observer:
                                type: string
                            timestamp:
                                type: integer
                            attributes:
                                type: object
                                additionalProperties:
                                    type: object
                                    properties:
                                        value:
                                            type: string
                                        created_at:
                                            type: integer
                                        created_by:
                                            type: string
                                        modified_at:
                                            type: integer
                                        modified_by:
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
                                example: False
                            comment:
                                type: string
                                example: 'ERROR_RETRIEVING_ATTRIBUTES'
    """
    ad_id = event['pathParameters']['ad_id']
    observer_id = event['pathParameters']['observer_id']
    timestamp = event['pathParameters']['timestamp']
    s3 = session.client('s3')
    ad_attributes_path = f'{AD_ATTRIBUTES_PREFIX}/{observer_id}_{timestamp}.{ad_id}.json'
    try:
        ad_attributes_object = s3.get_object(
            Bucket=META_BUCKET,
            Key=ad_attributes_path
        )
        ad_attributes_data = json.loads(ad_attributes_object['Body'].read().decode('utf-8'))
        return {
            "ad_id": ad_id,
            "observer": observer_id,
            "timestamp": timestamp,
            "attributes": ad_attributes_data
        }
    except Exception as e:
        return {
            "ad_id": ad_id,
            "observer": observer_id,
            "timestamp": timestamp,
            "attributes": {}
        }

@route('ads/{observer_id}/{timestamp}.{ad_id}/attributes', 'PUT')
@use(authenticate)
def add_properties(event, response):
    """Add or update ad attributes in the database.

    Add or update custom attributes for the specified ad in the database.
    ---
    tags:
        - ads/attributes
    parameters:
        - in: path
          name: observer_id
          required: true
          schema:
              type: string
        - in: path
          name: timestamp
          required: true
          schema:
              type: string
        - in: path
          name: ad_id
          required: true
          schema:
              type: string
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    properties:
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
                                example: False
                            comment:
                                type: string
                                example: 'AD_NOT_FOUND'
    """
    observer_id = event['pathParameters']['observer_id']
    timestamp = event['pathParameters']['timestamp']
    ad_id = event['pathParameters']['ad_id']
    attribute = event['body']['attribute']
    # Ensure the ad actually exists in the S3 bucket
    ad_path = f'{observer_id}/temp/{timestamp}.{ad_id}/'
    print('AD PATH:', ad_path)
    s3 = session.client('s3')
    try:
        # Ensure the folder exists
        s3.list_objects_v2(Bucket=ADS_BUCKET, Prefix=ad_path)
    except Exception as e:
        return response.status(400).json({
            "success": False,
            "comment": "AD_NOT_FOUND"
        })
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
    return {
        "success": True,
        "comment": "ATTRIBUTE_SET_SUCCESSFULLY"
    }

@route('ads/{observer_id}/{timestamp}.{ad_id}/attributes/{attribute_key}', 'GET')
@use(authenticate)
def get_single_attribute(event, response):
    """Retrieve a single attribute for an ad.

    Retrieve a specific custom attribute for the specified ad.
    ---
    tags:
        - ads/attributes
    parameters:
        - in: path
          name: observer_id
          required: true
          schema:
              type: string
        - in: path
          name: timestamp
          required: true
          schema:
              type: string
        - in: path
          name: ad_id
          required: true
          schema:
              type: string
        - in: path
          name: attribute_key
          required: true
          schema:
              type: string
    responses:
        200:
            description: A successful response
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            key:
                                type: string
                            value:
                                type: string
                            created_at:
                                type: integer
                            created_by:
                                type: string
                            modified_at:
                                type: integer
                            modified_by:
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
                                example: False
                            comment:
                                type: string
                                example: 'ATTRIBUTE_NOT_FOUND'
    """
    observer_id = event['pathParameters']['observer_id']
    timestamp = event['pathParameters']['timestamp']
    ad_id = event['pathParameters']['ad_id']
    attribute_key = event['pathParameters']['attribute_key']
    ad_attributes_path = f'{AD_ATTRIBUTES_PREFIX}/{observer_id}_{timestamp}.{ad_id}.json'
    s3 = session.client('s3')
    try:
        ad_attributes_object = s3.get_object(
            Bucket=META_BUCKET,
            Key=ad_attributes_path
        )
        ad_attributes_data = json.loads(ad_attributes_object['Body'].read().decode('utf-8'))
        if attribute_key in ad_attributes_data:
            return ad_attributes_data[attribute_key]
        else:
            return response.status(400).json({
                "success": False,
                "comment": "ATTRIBUTE_NOT_FOUND"
            })
    except Exception as e:
        return response.status(400).json({
            "success": False,
            "comment": "ERROR_RETRIEVING_ATTRIBUTE"
        })

@route('ads/{observer_id}/{timestamp}.{ad_id}/attributes/{attribute_key}', 'DELETE')
@use(authenticate)
def delete_properties(event, response):
    """Delete ad attributes from the database.

    Delete custom attributes for the specified ad in the database.
    ---
    tags:
        - ads/attributes
    parameters:
        - in: path
          name: observer_id
          required: true
          schema:
              type: string
        - in: path
          name: timestamp
          required: true
          schema:
              type: string
        - in: path
          name: ad_id
          required: true
          schema:
              type: string
        - in: path
          name: attribute_key
          required: true
          schema:
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
                                example: False
                            comment:
                                type: string
                                example: 'ERROR_DELETING_ATTRIBUTE'
    """
    observer_id = event['pathParameters']['observer']
    timestamp = event['pathParameters']['timestamp']
    ad_id = event['pathParameters']['ad_id']
    attribute_key = event['pathParameters']['attribute_key']
    ad_attributes_path = f'{AD_ATTRIBUTES_PREFIX}/{observer_id}_{timestamp}.{ad_id}.json'
    s3 = session.client('s3')
    try:
        ad_attributes_object = s3.get_object(
            Bucket=META_BUCKET,
            Key=ad_attributes_path
        )
        ad_attributes_data = json.loads(ad_attributes_object['Body'].read().decode('utf-8'))
        if attribute_key in ad_attributes_data:
            del ad_attributes_data[attribute_key]
            s3.put_object(
                Bucket=META_BUCKET,
                Key=ad_attributes_path,
                Body=json.dumps(ad_attributes_data).encode('utf-8')
            )
            return {
                "success": True,
                "comment": "ATTRIBUTE_DELETED"
            }
        else:
            return response.status(400).json({
                "success": False,
                "comment": "ATTRIBUTE_NOT_FOUND"
            })
    except Exception as e:
        return response.status(400).json({
            "success": False,
            "comment": "ERROR_DELETING_ATTRIBUTE"
        })