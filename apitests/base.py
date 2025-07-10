# Base file for testing the API endpoints.
import json
from typing import Literal
from lambda_function import lambda_handler as local_handler
from configparser import ConfigParser

from utils.hash_password import hash_password
# Need to access the database directly as without functional authentication, it is not possible to create users through the API (which needs authentication).
from db.shared_repositories import users_repository

config = ConfigParser()
config.read('config.ini')

username = config['TEST']['USERNAME']
password = config['TEST']['PASSWORD']



def create_test_user():
    """
    Create a test user for testing purposes.
    
    This function creates a test user with the specified username and password, and assigns it an admin role.
    """
    test_user = {
        'username': username,
        'password': hash_password(password),
        'full_name': 'Test User (Auto-generated)',
        'enabled': True,
        'role': 'admin'
    }
    with users_repository.create_session() as session:
        session.create(test_user)
    # users_repository.create(test_user)

def ensure_test_user_exists():
    """
    Ensure that a test user exists in the system.
    
    This function checks if a test user with the specified username exists. If not, it creates one.
    """
    try:
        # Attempt to get the user
        with users_repository.create_session() as session:
            user = session.get_first({'username': username})
            if user is None:
                create_test_user()
    except Exception as e:
        print(f"Error ensuring test user exists: {e}")

def get_login_token():
    ensure_test_user_exists()
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