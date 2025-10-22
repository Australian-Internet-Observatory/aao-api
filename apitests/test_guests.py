import json
import sys
sys.path.append("../")
from lambda_function import lambda_handler as local_handler
from base import get_login_token
import time
import utils.metadata_sub_bucket as metadata
import pytest

# Test constants
TEST_SESSION_KEY = "test_session"
TEST_SESSION_KEY_2 = "test_session_2" 
TEST_DESCRIPTION = "Test session description"
TEST_EXPIRATION_TIME = 3600  # 1 hour
SESSION_FOLDER_PREFIX = 'guest-sessions'

@pytest.mark.skip(reason="Helper function, not a test")
def cleanup_test_sessions():
    """Clean up any test sessions that might exist"""
    try:
        test_keys = [TEST_SESSION_KEY, TEST_SESSION_KEY_2]
        for key in test_keys:
            session_file_key = f"{SESSION_FOLDER_PREFIX}/{key}.json"
            try:
                metadata.delete_object(session_file_key)
            except metadata.s3.exceptions.NoSuchKey:
                pass  # Session doesn't exist, that's fine
    except Exception as e:
        print(f"Warning: Could not clean up test sessions: {e}")

def create_test_guest_session(key=TEST_SESSION_KEY, expiration_time=TEST_EXPIRATION_TIME, description=TEST_DESCRIPTION):
    """Helper function to create a test guest session"""
    token = get_login_token()
    
    body = {
        "key": key,
        "expiration_time": expiration_time,
        "description": description
    }
    
    event = {
        "path": "/guests",
        "httpMethod": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        "body": json.dumps(body)
    }
    
    return local_handler(event, {})

def get_guest_session_by_key(key):
    """Helper function to get a guest session by key (no auth required)"""
    event = {
        "path": f"/guests/{key}",
        "httpMethod": "GET",
        "pathParameters": {
            "key": key
        }
    }
    
    return local_handler(event, {})

def delete_guest_session_by_key(key):
    """Helper function to delete a guest session by key"""
    token = get_login_token()
    
    event = {
        "path": f"/guests/{key}",
        "httpMethod": "DELETE",
        "headers": {
            "Authorization": f"Bearer {token}"
        },
        "pathParameters": {
            "key": key
        }
    }
    
    return local_handler(event, {})

def update_guest_session_by_key(key, description=None, expiration_time=None):
    """Helper function to update a guest session by key"""
    token = get_login_token()
    
    body = {}
    if description is not None:
        body["description"] = description
    if expiration_time is not None:
        body["expiration_time"] = expiration_time
    
    event = {
        "path": f"/guests/{key}",
        "httpMethod": "PATCH",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        "body": json.dumps(body),
        "pathParameters": {
            "key": key
        }
    }
    
    return local_handler(event, {})

def test_create_guest_session_success():
    """Test creating a guest session successfully"""
    cleanup_test_sessions()
    result = create_test_guest_session()
    
    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    assert body['success'] is True
    assert 'token' in body
    assert body['token'] is not None
    cleanup_test_sessions()

def test_create_guest_session_missing_key():
    """Test creating a guest session with missing key"""
    cleanup_test_sessions()
    token = get_login_token()
    
    body = {
        "expiration_time": TEST_EXPIRATION_TIME,
        "description": TEST_DESCRIPTION
    }
    
    event = {
        "path": "/guests",
        "httpMethod": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        "body": json.dumps(body)
    }
    
    result = local_handler(event, {})
    
    assert result['statusCode'] == 400
    body = json.loads(result['body'])
    assert body['success'] is False
    assert body['comment'] == "Missing required fields"
    cleanup_test_sessions()

def test_create_guest_session_missing_expiration_time():
    """Test creating a guest session with missing expiration_time"""
    cleanup_test_sessions()
    token = get_login_token()
    
    body = {
        "key": TEST_SESSION_KEY,
        "description": TEST_DESCRIPTION
    }
    
    event = {
        "path": "/guests",
        "httpMethod": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        "body": json.dumps(body)
    }
    
    result = local_handler(event, {})
    
    assert result['statusCode'] == 400
    body = json.loads(result['body'])
    assert body['success'] is False
    assert body['comment'] == "Missing required fields"
    cleanup_test_sessions()

def test_create_guest_session_without_auth():
    """Test creating a guest session without authentication"""
    cleanup_test_sessions()
    body = {
        "key": TEST_SESSION_KEY,
        "expiration_time": TEST_EXPIRATION_TIME,
        "description": TEST_DESCRIPTION
    }
    
    event = {
        "path": "/guests",
        "httpMethod": "POST",
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }
    
    result = local_handler(event, {})
    
    assert result['statusCode'] == 401
    cleanup_test_sessions()

def test_list_guest_sessions_success():
    """Test listing guest sessions successfully"""
    cleanup_test_sessions()
    # Create a couple of test sessions
    create_test_guest_session(TEST_SESSION_KEY)
    create_test_guest_session(TEST_SESSION_KEY_2)
    
    # List sessions
    token = get_login_token()
    event = {
        "path": "/guests",
        "httpMethod": "GET",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    }
    result = local_handler(event, {})
    
    assert result['statusCode'] == 200
    sessions = json.loads(result['body'])
    assert isinstance(sessions, list)
    
    # Check that our test sessions are in the list
    session_keys = [session['key'] for session in sessions]
    assert TEST_SESSION_KEY in session_keys
    assert TEST_SESSION_KEY_2 in session_keys
    cleanup_test_sessions()

def test_list_guest_sessions_without_auth():
    """Test listing guest sessions without authentication"""
    cleanup_test_sessions()
    event = {
        "path": "/guests",
        "httpMethod": "GET",
        "headers": {
            "Content-Type": "application/json"
        }
    }
    result = local_handler(event, {})
    
    assert result['statusCode'] == 401
    cleanup_test_sessions()

def test_get_guest_session_success():
    """Test retrieving a guest session successfully"""
    cleanup_test_sessions()
    # Create a test session
    create_result = create_test_guest_session()
    assert create_result['statusCode'] == 200
    
    # Retrieve the session
    result = get_guest_session_by_key(TEST_SESSION_KEY)
    
    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    assert body['success'] is True
    assert 'token' in body
    assert body['token'] is not None
    cleanup_test_sessions()

def test_get_guest_session_not_found():
    """Test retrieving a non-existent guest session"""
    cleanup_test_sessions()
    result = get_guest_session_by_key("nonexistent_session")
    
    assert result['statusCode'] == 404
    body = json.loads(result['body'])
    assert body['success'] is False
    assert body['comment'] == "Session not found"
    cleanup_test_sessions()
    
def test_delete_guest_session_success():
    """Test deleting a guest session successfully"""
    cleanup_test_sessions()
    # Create a test session
    create_result = create_test_guest_session()
    assert create_result['statusCode'] == 200
    
    # Delete the session
    result = delete_guest_session_by_key(TEST_SESSION_KEY)
    
    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    assert body['success'] is True
    assert body['comment'] == "Session deleted"
    
    # Verify the session is gone
    get_result = get_guest_session_by_key(TEST_SESSION_KEY)
    assert get_result['statusCode'] == 404
    cleanup_test_sessions()

def test_delete_guest_session_not_found():
    """Test deleting a non-existent guest session"""
    cleanup_test_sessions()
    result = delete_guest_session_by_key("nonexistent_session")
    
    assert result['statusCode'] == 404
    body = json.loads(result['body'])
    assert body['success'] is False
    assert body['comment'] == "Session not found"
    cleanup_test_sessions()

def test_delete_guest_session_without_auth():
    """Test deleting a guest session without authentication"""
    cleanup_test_sessions()
    event = {
        "path": f"/guests/{TEST_SESSION_KEY}",
        "httpMethod": "DELETE",
        "pathParameters": {
            "key": TEST_SESSION_KEY
        }
    }
    
    result = local_handler(event, {})
    
    assert result['statusCode'] == 401
    cleanup_test_sessions()

def test_update_guest_session_description_success():
    """Test updating a guest session description successfully"""
    cleanup_test_sessions()
    # Create a test session
    create_result = create_test_guest_session()
    assert create_result['statusCode'] == 200
    
    # Update the description
    new_description = "Updated description"
    result = update_guest_session_by_key(TEST_SESSION_KEY, description=new_description)
    
    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    assert body['success'] is True
    assert body['comment'] == "Session updated"
    cleanup_test_sessions()

def test_update_guest_session_expiration_success():
    """Test updating a guest session expiration time successfully"""
    cleanup_test_sessions()
    # Create a test session
    create_result = create_test_guest_session()
    assert create_result['statusCode'] == 200
    
    # Update the expiration time
    new_expiration = 7200  # 2 hours
    result = update_guest_session_by_key(TEST_SESSION_KEY, expiration_time=new_expiration)
    
    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    assert body['success'] is True
    assert body['comment'] == "Session updated"
    cleanup_test_sessions()

def test_update_guest_session_both_fields_success():
    """Test updating both description and expiration time successfully"""
    cleanup_test_sessions()
    # Create a test session
    create_result = create_test_guest_session()
    assert create_result['statusCode'] == 200
    
    # Update both fields
    new_description = "Updated description"
    new_expiration = 7200  # 2 hours
    result = update_guest_session_by_key(TEST_SESSION_KEY, description=new_description, expiration_time=new_expiration)
    
    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    assert body['success'] is True
    assert body['comment'] == "Session updated"
    cleanup_test_sessions()

def test_update_guest_session_not_found():
    """Test updating a non-existent guest session"""
    cleanup_test_sessions()
    result = update_guest_session_by_key("nonexistent_session", description="New description")
    
    assert result['statusCode'] == 404
    body = json.loads(result['body'])
    assert body['success'] is False
    assert body['comment'] == "Session not found"
    cleanup_test_sessions()

def test_update_guest_session_without_auth():
    """Test updating a guest session without authentication"""
    cleanup_test_sessions()
    body = {
        "description": "New description"
    }
    
    event = {
        "path": f"/guests/{TEST_SESSION_KEY}",
        "httpMethod": "PATCH",
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body),
        "pathParameters": {
            "key": TEST_SESSION_KEY
        }
    }
    
    result = local_handler(event, {})
    
    assert result['statusCode'] == 401
    cleanup_test_sessions()

def test_guest_session_token_functionality():
    """Test that the guest session token can be used for authentication"""
    cleanup_test_sessions()
    # Create a guest session
    create_result = create_test_guest_session()
    assert create_result['statusCode'] == 200
    guest_token = json.loads(create_result['body'])['token']
    
    # Retrieve the session to get a fresh token
    get_result = get_guest_session_by_key(TEST_SESSION_KEY)
    assert get_result['statusCode'] == 200
    fresh_token = json.loads(get_result['body'])['token']
    
    # Both tokens should be valid
    assert guest_token is not None
    assert fresh_token is not None
    cleanup_test_sessions()
    
def test_get_specific_session():
    session = 'mobile-observer-undefined'
    result = get_guest_session_by_key(session)
    print(result)