import json
import pytest
from base import execute_endpoint, get_login_token
from lambda_function import lambda_handler as local_handler

# Test data
TEST_OBSERVER_ID = "test_observer"
TEST_TIMESTAMP = "1234567890"
TEST_AD_ID = "test_ad_123"
TEST_ATTRIBUTE_KEY = "test_attribute"
TEST_ATTRIBUTE_VALUE = "test_value"

def create_test_attribute(observer_id=TEST_OBSERVER_ID, 
                         timestamp=TEST_TIMESTAMP, 
                         ad_id=TEST_AD_ID, 
                         key=TEST_ATTRIBUTE_KEY, 
                         value=TEST_ATTRIBUTE_VALUE):
    """Helper function to create a test attribute"""
    token = get_login_token()
    endpoint = f"ads/{observer_id}/{timestamp}.{ad_id}/attributes"
    body = {
        "attribute": {
            "key": key,
            "value": value
        }
    }
    
    event = {
        "path": f"/{endpoint}",
        "httpMethod": "PUT",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        "body": json.dumps(body),
        "pathParameters": {
            "observer_id": observer_id,
            "timestamp": timestamp,
            "ad_id": ad_id
        }
    }
    
    return local_handler(event, {})

def delete_test_attribute(observer_id=TEST_OBSERVER_ID, 
                         timestamp=TEST_TIMESTAMP, 
                         ad_id=TEST_AD_ID, 
                         key=TEST_ATTRIBUTE_KEY):
    """Helper function to delete a test attribute"""
    token = get_login_token()
    endpoint = f"ads/{observer_id}/{timestamp}.{ad_id}/attributes/{key}"
    
    event = {
        "path": f"/{endpoint}",
        "httpMethod": "DELETE",
        "headers": {
            "Authorization": f"Bearer {token}"
        },
        "pathParameters": {
            "observer_id": observer_id,
            "timestamp": timestamp,
            "ad_id": ad_id,
            "attribute_key": key
        }
    }
    
    return local_handler(event, {})

class TestAdAttributes:
    """Test class for ad attributes endpoints"""
    
    def test_create_attribute_success(self):
        """Test creating a new attribute successfully"""
        # Clean up any existing attribute first
        try:
            delete_test_attribute()
        except:
            pass
            
        result = create_test_attribute()
        
        print(f"Status Code: {result['statusCode']}")
        print(f"Response Body: {result.get('body', 'No body')}")
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['success'] == True
        assert body['comment'] == "ATTRIBUTE_SET_SUCCESSFULLY"
        
        # Clean up
        delete_test_attribute()
    
    def test_create_attribute_unauthorized(self):
        """Test creating attribute without authentication"""
        endpoint = f"ads/{TEST_OBSERVER_ID}/{TEST_TIMESTAMP}.{TEST_AD_ID}/attributes"
        body = {
            "attribute": {
                "key": TEST_ATTRIBUTE_KEY,
                "value": TEST_ATTRIBUTE_VALUE
            }
        }
        
        event = {
            "path": f"/{endpoint}",
            "httpMethod": "PUT",
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(body),
            "pathParameters": {
                "observer_id": TEST_OBSERVER_ID,
                "timestamp": TEST_TIMESTAMP,
                "ad_id": TEST_AD_ID
            }
        }
        
        result = local_handler(event, {})
        assert result['statusCode'] == 401
    
    def test_update_existing_attribute(self):
        """Test updating an existing attribute"""
        # Create initial attribute
        create_test_attribute()
        
        # Update with new value
        new_value = "updated_test_value"
        result = create_test_attribute(value=new_value)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['success'] == True
        assert body['comment'] == "ATTRIBUTE_SET_SUCCESSFULLY"
        
        # Verify the update by getting the attribute
        token = get_login_token()
        endpoint = f"ads/{TEST_OBSERVER_ID}/{TEST_TIMESTAMP}.{TEST_AD_ID}/attributes/{TEST_ATTRIBUTE_KEY}"
        
        event = {
            "path": f"/{endpoint}",
            "httpMethod": "GET",
            "headers": {
                "Authorization": f"Bearer {token}"
            },
            "pathParameters": {
                "observer_id": TEST_OBSERVER_ID,
                "timestamp": TEST_TIMESTAMP,
                "ad_id": TEST_AD_ID,
                "attribute_key": TEST_ATTRIBUTE_KEY
            }
        }
        
        get_result = local_handler(event, {})
        assert get_result['statusCode'] == 200
        get_body = json.loads(get_result['body'])
        assert get_body['value'] == new_value
        
        # Clean up
        delete_test_attribute()
    
    def test_get_all_attributes_success(self):
        """Test getting all attributes for an ad"""
        # Create multiple test attributes
        create_test_attribute(key="attr1", value="value1")
        create_test_attribute(key="attr2", value="value2")
        
        token = get_login_token()
        endpoint = f"ads/{TEST_OBSERVER_ID}/{TEST_TIMESTAMP}.{TEST_AD_ID}/attributes"
        
        event = {
            "path": f"/{endpoint}",
            "httpMethod": "GET",
            "headers": {
                "Authorization": f"Bearer {token}"
            },
            "pathParameters": {
                "observer_id": TEST_OBSERVER_ID,
                "timestamp": TEST_TIMESTAMP,
                "ad_id": TEST_AD_ID
            }
        }
        
        result = local_handler(event, {})
        assert result['statusCode'] == 200
        
        body = json.loads(result['body'])
        assert body['ad_id'] == TEST_AD_ID
        assert body['observer'] == TEST_OBSERVER_ID
        assert body['timestamp'] == int(TEST_TIMESTAMP)
        assert 'attributes' in body
        
        # Should have at least the attributes we created
        attributes = body['attributes']
        assert 'attr1' in attributes
        assert 'attr2' in attributes
        assert attributes['attr1']['value'] == 'value1'
        assert attributes['attr2']['value'] == 'value2'
        
        # Clean up
        delete_test_attribute(key="attr1")
        delete_test_attribute(key="attr2")
    
    def test_get_all_attributes_empty(self):
        """Test getting all attributes when none exist"""
        token = get_login_token()
        endpoint = f"ads/{TEST_OBSERVER_ID}/{TEST_TIMESTAMP}.{TEST_AD_ID}/attributes"
        
        event = {
            "path": f"/{endpoint}",
            "httpMethod": "GET",
            "headers": {
                "Authorization": f"Bearer {token}"
            },
            "pathParameters": {
                "observer_id": TEST_OBSERVER_ID,
                "timestamp": TEST_TIMESTAMP,
                "ad_id": TEST_AD_ID
            }
        }
        
        result = local_handler(event, {})
        assert result['statusCode'] == 200
        
        body = json.loads(result['body'])
        assert body['attributes'] == {}
    
    def test_get_single_attribute_success(self):
        """Test getting a single attribute successfully"""
        # Create test attribute
        create_test_attribute()
        
        token = get_login_token()
        endpoint = f"ads/{TEST_OBSERVER_ID}/{TEST_TIMESTAMP}.{TEST_AD_ID}/attributes/{TEST_ATTRIBUTE_KEY}"
        
        event = {
            "path": f"/{endpoint}",
            "httpMethod": "GET",
            "headers": {
                "Authorization": f"Bearer {token}"
            },
            "pathParameters": {
                "observer_id": TEST_OBSERVER_ID,
                "timestamp": TEST_TIMESTAMP,
                "ad_id": TEST_AD_ID,
                "attribute_key": TEST_ATTRIBUTE_KEY
            }
        }
        
        result = local_handler(event, {})
        assert result['statusCode'] == 200
        
        body = json.loads(result['body'])
        assert body['key'] == TEST_ATTRIBUTE_KEY
        assert body['value'] == TEST_ATTRIBUTE_VALUE
        assert 'created_at' in body
        assert 'created_by' in body
        assert 'modified_at' in body
        assert 'modified_by' in body
        
        # Clean up
        delete_test_attribute()
    
    def test_get_single_attribute_not_found(self):
        """Test getting a single attribute that doesn't exist"""
        token = get_login_token()
        endpoint = f"ads/{TEST_OBSERVER_ID}/{TEST_TIMESTAMP}.{TEST_AD_ID}/attributes/nonexistent_key"
        
        event = {
            "path": f"/{endpoint}",
            "httpMethod": "GET",
            "headers": {
                "Authorization": f"Bearer {token}"
            },
            "pathParameters": {
                "observer_id": TEST_OBSERVER_ID,
                "timestamp": TEST_TIMESTAMP,
                "ad_id": TEST_AD_ID,
                "attribute_key": "nonexistent_key"
            }
        }
        
        result = local_handler(event, {})
        assert result['statusCode'] == 400
        
        body = json.loads(result['body'])
        assert body['success'] == False
        assert body['comment'] == "ATTRIBUTE_NOT_FOUND"
    
    def test_delete_attribute_success(self):
        """Test deleting an attribute successfully"""
        # Create test attribute
        create_test_attribute()
        
        # Delete the attribute
        result = delete_test_attribute()
        assert result['statusCode'] == 200
        
        body = json.loads(result['body'])
        assert body['success'] == True
        assert body['comment'] == "ATTRIBUTE_DELETED"
        
        # Verify it's actually deleted by trying to get it
        token = get_login_token()
        endpoint = f"ads/{TEST_OBSERVER_ID}/{TEST_TIMESTAMP}.{TEST_AD_ID}/attributes/{TEST_ATTRIBUTE_KEY}"
        
        event = {
            "path": f"/{endpoint}",
            "httpMethod": "GET",
            "headers": {
                "Authorization": f"Bearer {token}"
            },
            "pathParameters": {
                "observer_id": TEST_OBSERVER_ID,
                "timestamp": TEST_TIMESTAMP,
                "ad_id": TEST_AD_ID,
                "attribute_key": TEST_ATTRIBUTE_KEY
            }
        }
        
        get_result = local_handler(event, {})
        assert get_result['statusCode'] == 400
    
    def test_delete_attribute_not_found(self):
        """Test deleting an attribute that doesn't exist"""
        result = delete_test_attribute(key="nonexistent_key")
        assert result['statusCode'] == 400
        
        body = json.loads(result['body'])
        assert body['success'] == False
        assert body['comment'] == "ATTRIBUTE_NOT_FOUND"
    
    def test_delete_attribute_unauthorized(self):
        """Test deleting attribute without authentication"""
        endpoint = f"ads/{TEST_OBSERVER_ID}/{TEST_TIMESTAMP}.{TEST_AD_ID}/attributes/{TEST_ATTRIBUTE_KEY}"
        
        event = {
            "path": f"/{endpoint}",
            "httpMethod": "DELETE",
            "pathParameters": {
                "observer_id": TEST_OBSERVER_ID,
                "timestamp": TEST_TIMESTAMP,
                "ad_id": TEST_AD_ID,
                "attribute_key": TEST_ATTRIBUTE_KEY
            }
        }
        
        result = local_handler(event, {})
        assert result['statusCode'] == 401
    
    def test_attribute_audit_fields(self):
        """Test that audit fields (created_by, modified_by, etc.) are properly set"""
        # Create test attribute
        create_test_attribute()
        
        # Get the attribute and verify audit fields
        token = get_login_token()
        endpoint = f"ads/{TEST_OBSERVER_ID}/{TEST_TIMESTAMP}.{TEST_AD_ID}/attributes/{TEST_ATTRIBUTE_KEY}"
        
        event = {
            "path": f"/{endpoint}",
            "httpMethod": "GET",
            "headers": {
                "Authorization": f"Bearer {token}"
            },
            "pathParameters": {
                "observer_id": TEST_OBSERVER_ID,
                "timestamp": TEST_TIMESTAMP,
                "ad_id": TEST_AD_ID,
                "attribute_key": TEST_ATTRIBUTE_KEY
            }
        }
        
        result = local_handler(event, {})
        assert result['statusCode'] == 200
        
        body = json.loads(result['body'])
        
        # Check that audit fields are present and non-empty
        assert 'created_at' in body
        assert 'created_by' in body
        assert 'modified_at' in body
        assert 'modified_by' in body
        
        assert isinstance(body['created_at'], int)
        assert isinstance(body['modified_at'], int)
        assert body['created_at'] > 0
        assert body['modified_at'] > 0
        assert len(body['created_by']) > 0
        assert len(body['modified_by']) > 0
        
        # For a newly created attribute, created_at should equal modified_at
        assert body['created_at'] == body['modified_at']
        assert body['created_by'] == body['modified_by']
        
        # Clean up
        delete_test_attribute()
    
    def test_multiple_attributes_same_ad(self):
        """Test handling multiple attributes for the same ad"""
        # Create multiple attributes
        attributes = [
            ("name", "Test Product"),
            ("price", "19.99"),
            ("category", "Electronics"),
            ("description", "A test product")
        ]
        
        # Create all attributes
        for key, value in attributes:
            create_test_attribute(key=key, value=value)
        
        # Get all attributes
        token = get_login_token()
        endpoint = f"ads/{TEST_OBSERVER_ID}/{TEST_TIMESTAMP}.{TEST_AD_ID}/attributes"
        
        event = {
            "path": f"/{endpoint}",
            "httpMethod": "GET",
            "headers": {
                "Authorization": f"Bearer {token}"
            },
            "pathParameters": {
                "observer_id": TEST_OBSERVER_ID,
                "timestamp": TEST_TIMESTAMP,
                "ad_id": TEST_AD_ID
            }
        }
        
        result = local_handler(event, {})
        assert result['statusCode'] == 200
        
        body = json.loads(result['body'])
        retrieved_attributes = body['attributes']
        
        # Verify all attributes are present
        for key, value in attributes:
            assert key in retrieved_attributes
            assert retrieved_attributes[key]['value'] == value
        
        # Clean up
        for key, _ in attributes:
            delete_test_attribute(key=key)

def test_hide_ad():
    ad = {
        "observer_id": "4ccd5b4b-19da-4a34-a627-c9a534a627cd",
        "timestamp": "1748229356094",
        "ad_id": "851e2cf8-5a82-48ad-805b-88f84754f462",
    }
    response = execute_endpoint(
        f"ads/{ad['observer_id']}/{ad['timestamp']}.{ad['ad_id']}/attributes",
        "PUT",
        {
            "attribute": {
                "key": "hidden",
                "value": "True"
            }
        },
        auth=True
    )
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
    
def test_unhide_ad():
    ad = {
        "observer_id": "4ccd5b4b-19da-4a34-a627-c9a534a627cd",
        "timestamp": "1748229356094",
        "ad_id": "851e2cf8-5a82-48ad-805b-88f84754f462",
    }
    response = execute_endpoint(
        f"ads/{ad['observer_id']}/{ad['timestamp']}.{ad['ad_id']}/attributes",
        "PUT",
        {
            "attribute": {
                "key": "hidden",
                "value": "False"
            }
        },
        auth=True
    )
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"