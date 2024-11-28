from . import authenticate

import json
import base64
import boto3

from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

session_us_east = boto3.Session(
    region_name='us-east-2',
    aws_access_key_id=config['AWS']['ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS']['SECRET_ACCESS_KEY']
)

def parse_body(event_raw, context, response):
    event = event_raw
    try:
        if ("body" in event_raw):
            # ...decode the request body from the API
            request_body = event_raw['body']
            event['body'] = json.loads(request_body)
        else:
            event = event_raw
    except Exception as e:
        event = event_raw
  
    return (event, response, context)