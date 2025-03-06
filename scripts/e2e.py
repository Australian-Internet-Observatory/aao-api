# Ensure the lambda function is deployed

import json
import boto3

from configparser import ConfigParser
config = ConfigParser()
config.read('config.ini')

session = boto3.Session(
    aws_access_key_id=config['AWS']['ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS']['SECRET_ACCESS_KEY']
)

lambda_client = session.client('lambda', region_name=config['AWS']['REGION'])

function_name = config['DEPLOYMENT']['LAMBDA_FUNCTION_NAME']

def invoke_lambda():
    event = {
        'path': 'hello',
        'httpMethod': 'GET',
        'headers': {
            'Content-Type': 'application/json',
        }
    }
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )
    payload = json.loads(response['Payload'].read())
    print(json.dumps(payload, indent=2))
    
invoke_lambda()