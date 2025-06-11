# Base file for testing the API endpoints.
import json
from typing import Literal
from lambda_function import lambda_handler as local_handler
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

username = config['TEST']['USERNAME']
password = config['TEST']['PASSWORD']

def get_login_token():
    data = {
        'username': username,
        'password': password
    }
    event = {
        'path': '/auth/login',
        'httpMethod': 'POST',
        'body': json.dumps(data)
    }
    response = local_handler(event, None)
    return json.loads(response['body'])['token']

def execute_endpoint(endpoint:str, 
                     method: Literal['GET', 'POST', 'DELETE', 'PUT', 'PATCH']='GET', 
                     body:dict | None = None, 
                     headers:dict | None = None, 
                     auth = False
                    ):
    """
    Execute a local API endpoint with the given method and body.
    
    :param endpoint: The API endpoint to call.
    :param method: The HTTP method to use (default is 'GET').
    :param body: The request body (default is None).
    :param headers: Additional headers to include in the request (default is None).
    :return: The response from the API call.
    """
    if auth:
        token = get_login_token()
        headers = headers or {}
        headers['Authorization'] = f'Bearer {token}'
    
    event = {
        'httpMethod': method,
        'path': endpoint,
        'headers': headers or {},
    }
    
    if body is not None:
        event['body'] = json.dumps(body)
    
    response = local_handler(event, None)
    if 'body' in response and response['body'] is not None:
        response['body'] = json.loads(response['body'])
    return response