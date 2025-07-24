# Ensure the lambda function is deployed

import json
import boto3

import json
import boto3

from config import config

session = boto3.Session(
    aws_access_key_id=config.aws.access_key_id,
    aws_secret_access_key=config.aws.secret_access_key
)

lambda_client = session.client('lambda', region_name=config.aws.region)

function_name = config.deployment.lambda_function_name

def invoke_lambda():
    event = {
        "path": "/hello",
        "httpMethod": "GET",
        "isBase64Encoded": True
    }
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )
    payload = json.loads(response['Payload'].read())
    print(json.dumps(payload, indent=2))
    assert payload['statusCode'] == 200
    
invoke_lambda()