import json
# Needed for importing the lambda_function module
import sys
sys.path.append("../")
from lambda_function import lambda_handler as local_handler
from config import config
import pytest
import requests

username = config.test.username
password = config.test.password

@pytest.mark.skip(reason="Helper function, not a test")
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

def test_get_ads():
    token = get_login_token()
    headers = {
        'Authorization': f'Bearer {token}'
    }
    respones = local_handler({
        'path': '/ads',
        'httpMethod': 'GET',
        'headers': headers
    }, None)
    print(respones)
    assert respones['statusCode'] == 200, f"Expected 200, got {respones['statusCode']}"
    body: dict = json.loads(respones['body'])
    presigned_url = body.get('presigned_url')
    # Check if presigned_url is a string
    assert isinstance(presigned_url, str), f"Expected string, got {type(presigned_url)}"
    
    # Fetch the presigned URL
    response = requests.get(presigned_url)
    # Check if the response is successful
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    # Check if the content is a list
    ads = response.json()
    assert isinstance(ads, list), f"Expected list, got {type(ads)}" 