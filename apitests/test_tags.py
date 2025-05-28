import json
# Needed for importing the lambda_function module
import sys
sys.path.append("../")
from lambda_function import lambda_handler as local_handler
from configparser import ConfigParser
import pytest
import requests

config = ConfigParser()
config.read('config.ini')

username = config['TEST']['USERNAME']
password = config['TEST']['PASSWORD']

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

@pytest.mark.skip(reason="Helper function, not a test")
def create_tag(tag={
    "name": "Test Tag",
    "description": "This is a test tag",
    "hex": "#FFFFFF"
}):
    token = get_login_token()
    event = {
        "path": "/tags",
        "httpMethod": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        "body": tag
    }
    result = local_handler(event, {})
    return result

def delete_tag(tag_id):
    token = get_login_token()
    event = {
        "path": f"/tags/{tag_id}",
        "httpMethod": "DELETE",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    }
    result = local_handler(event, {})
    return result

def test_create_and_delete_tag():
    result = create_tag({
        "name": "Test Tag",
        "description": "This is a test tag",
        "hex": "#FFFFFF"
    })
    assert result['statusCode'] == 201, f"Expected 201, got {result['statusCode']}"
    body = json.loads(result['body'])
    assert 'tag' in body, "Response should contain 'tag' key"
    tag_id = body['tag']['id']
    delete_result = delete_tag(tag_id)
    assert delete_result['statusCode'] == 200, f"Expected 200, got {delete_result['statusCode']}"

def test_list_tags():
    tags = [
        {
            "name": "Tag 1",
            "description": "This is tag 1",
            "hex": "#FF0000"
        },
        {
            "name": "Tag 2",
            "description": "This is tag 2",
            "hex": "#00FF00"
        },
        {
            "name": "Tag 3",
            "description": "This is tag 3",
            "hex": "#0000FF"
        }
    ]
    created_tags = []
    for tag in tags:
        result = create_tag(tag)
        assert result['statusCode'] == 201, f"Expected 201, got {result['statusCode']}"
        body = json.loads(result['body'])
        assert 'tag' in body, "Response should contain 'tag' key"
        created_tags.append(body['tag'])
    
    # List all tags
    token = get_login_token()
    event = {
        "path": "/tags",
        "httpMethod": "GET",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    }
    result = local_handler(event, {})
    assert result['statusCode'] == 200, f"Expected 200, got {result['statusCode']}"
    body = json.loads(result['body'])
    assert isinstance(body, list), "Response should be a list of tags"
    assert len(body) >= len(tags), "Response should contain at least the created tags"
    # Clean up created tags
    for tag in created_tags:
        delete_result = delete_tag(tag['id'])
        assert delete_result['statusCode'] == 200, f"Expected 200, got {delete_result['statusCode']}"

def test_update_tag():
    # Create a tag to update
    tag = {
        "name": "Tag to Update",
        "description": "This is a tag to update",
        "hex": "#FFFFFF"
    }
    result = create_tag(tag)
    assert result['statusCode'] == 201, f"Expected 201, got {result['statusCode']}"
    body = json.loads(result['body'])
    assert 'tag' in body, "Response should contain 'tag' key"
    tag_id = body['tag']['id']

    # Update the tag
    updated_tag = {
        "name": "Updated Tag",
        "description": "This is an updated tag",
        "hex": "#000000"
    }
    token = get_login_token()
    event = {
        "path": f"/tags/{tag_id}",
        "httpMethod": "PUT",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        "body": updated_tag
    }
    update_result = local_handler(event, {})
    assert update_result['statusCode'] == 200, f"Expected 200, got {update_result['statusCode']}"
    
    # Verify the update
    get_event = {
        "path": f"/tags/{tag_id}",
        "httpMethod": "GET",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    }
    get_result = local_handler(get_event, {})
    assert get_result['statusCode'] == 200, f"Expected 200, got {get_result['statusCode']}"
    get_body = json.loads(json.loads(get_result['body']))
    assert get_body['name'] == updated_tag['name'], "Tag name should be updated"
    assert get_body['description'] == updated_tag['description'], "Tag description should be updated"
    assert get_body['hex'] == updated_tag['hex'], "Tag hex should be updated"
    
    # Clean up
    delete_result = delete_tag(tag_id)
    assert delete_result['statusCode'] == 200, f"Expected 200, got {delete_result['statusCode']}"

example_ad = {
    "observer_id": "9e194bee-46ac-4fd9-ac6e-a11b4dcfc18c",
    "ad_id": "545ba836-81fe-4861-bc2e-6c8bfbe4e587",
    "timestamp": "1744851600298"
}

@pytest.mark.skip(reason="Helper function, not a test")
def get_tags_for_ad(ad=example_ad):
    token = get_login_token()
    event = {
        "path": f"/ads/{ad['observer_id']}/{ad['timestamp']}.{ad['ad_id']}/tags",
        "httpMethod": "GET",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    }
    result = local_handler(event, {})
    return result

def test_apply_tag():
    # Create a tag to apply
    tag = {
        "name": "Tag to Apply",
        "description": "This is a tag to apply",
        "hex": "#FFFFFF"
    }
    result = create_tag(tag)
    assert result['statusCode'] == 201, f"Expected 201, got {result['statusCode']}"
    body = json.loads(result['body'])
    assert 'tag' in body, "Response should contain 'tag' key"
    tag_id = body['tag']['id']

    # Apply the tag to an ad
    token = get_login_token()
    event = {
        "path": f"/ads/{example_ad['observer_id']}/{example_ad['timestamp']}.{example_ad['ad_id']}/tags",
        "httpMethod": "PUT",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        "body": json.dumps({"tag_ids": [tag_id]})
    }
    apply_result = local_handler(event, {})
    print(apply_result)
    assert apply_result['statusCode'] == 200, f"Expected 200, got {apply_result['statusCode']}"
    body = json.loads(apply_result['body'])
    assert 'success' in body, "Response should contain 'success' key"
    assert body['success'] is True, "Response should indicate success"

    # Verify the tag is applied to the ad
    get_result = get_tags_for_ad(example_ad)
    assert get_result['statusCode'] == 200, f"Expected 200, got {get_result['statusCode']}"
    body = json.loads(get_result['body'])
    tag_ids = body.get('tag_ids')
    assert isinstance(tag_ids, list), f"Response tag_ids should be a list of tag IDs, got {type(tag_ids)}"

    # Clean up
    delete_result = delete_tag(tag_id)
    assert delete_result['statusCode'] == 200, f"Expected 200, got {delete_result['statusCode']}"

def test_unapply_tag():
    # Create a tag to apply
    tag = {
        "name": "Tag to Unapply",
        "description": "This is a tag to unapply",
        "hex": "#FFFFFF"
    }
    result = create_tag(tag)
    assert result['statusCode'] == 201, f"Expected 201, got {result['statusCode']}"
    body = json.loads(result['body'])
    assert 'tag' in body, "Response should contain 'tag' key"
    tag_id = body['tag']['id']

    # Apply the tag to an ad
    token = get_login_token()
    event = {
        "path": f"/ads/{example_ad['observer_id']}/{example_ad['timestamp']}.{example_ad['ad_id']}/tags",
        "httpMethod": "PUT",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        "body": json.dumps({"tag_ids": [tag_id]})
    }
    apply_result = local_handler(event, {})
    assert apply_result['statusCode'] == 200, f"Expected 200, got {apply_result['statusCode']}"
    
    # Unapply the tag from the ad
    event = {
        "path": f"/ads/{example_ad['observer_id']}/{example_ad['timestamp']}.{example_ad['ad_id']}/tags",
        "httpMethod": "PUT",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        "body": json.dumps({"tag_ids": []})
    }
    unapply_result = local_handler(event, {})
    assert unapply_result['statusCode'] == 200, f"Expected 200, got {unapply_result['statusCode']}"
    
    # Verify the tag is removed from the ad
    get_result = get_tags_for_ad(example_ad)
    assert get_result['statusCode'] == 200, f"Expected 200, got {get_result['statusCode']}"
    body = json.loads(get_result['body'])
    tag_ids = body.get('tag_ids')
    assert isinstance(tag_ids, list), f"Response tag_ids should be a list of tag IDs, got {type(tag_ids)}"
    
    # Clean up
    delete_result = delete_tag(tag_id)
    assert delete_result['statusCode'] == 200, f"Expected 200, got {delete_result['statusCode']}"

@pytest.mark.skip(reason="No assertions in this test")
def test_get_tags_for_multiple_ads():
    # Endpoint: ads/batch/presign
    payload = {
        "ads": [
            {
                "ad_id": "545ba836-81fe-4861-bc2e-6c8bfbe4e587",
                "observer_id": "9e194bee-46ac-4fd9-ac6e-a11b4dcfc18c",
                "timestamp": "1744851600298"
            }
        ],
        "metadata_types": [
            "attributes",
            "tags"
        ]
    }
    
    token = get_login_token()
    event = {
        "path": "/ads/batch/presign",
        "httpMethod": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        "body": json.dumps(payload)
    }
    result = local_handler(event, {})
    # Get the presigned URL for the ads
    presigned_url = json.loads(result['body'])['presigned_url']
    print(f"Fetching from presigned URL: {presigned_url}")
    response = requests.get(presigned_url)
    content = response.json()
    print(f"Response from presigned URL: {content}")

if __name__ == "__main__":
    test_get_tags_for_multiple_ads()