from base import execute_endpoint
from utils.hash_password import hash_password
import time

# Need to access the database directly as without functional authentication, it is not possible to create users through the API (which needs authentication).
from db.shared_repositories import users_repository, user_identities_repository

def create_test_user(username: str = 'testuser'):
    """
    Create a test user for testing purposes.
    
    :return: The response from the API call.
    """
    # Create user in users table
    user_data = {
        'full_name': 'Test User',
        'enabled': True,
        'role': 'user'
    }
    with users_repository.create_session() as user_session:
        user_entity = user_session.create(user_data)
        user_id = user_entity['id']
    
    # Create identity in user_identities table
    with user_identities_repository.create_session() as identity_session:
        identity_data = {
            'user_id': user_id,
            'provider': 'local',
            'provider_user_id': username,
            'password': hash_password('testpassword'),
            'created_at': int(time.time())
        }
        identity_session.create(identity_data)

def delete_user(username: str):
    """
    Delete a user by username.
    
    :param username: The username of the user to delete.
    :return: The response from the API call.
    """
    # Find user identity by username
    with user_identities_repository.create_session() as identity_session:
        user_identity = identity_session.get_first({
            'provider': 'local',
            'provider_user_id': username
        })
        
        if user_identity is not None:
            user_id = user_identity.user_id
            
            # Delete the identity record
            identity_session.delete({
                'user_id': user_id,
                'provider': 'local'
            })
            
            # Check if user has other identities
            remaining_identities = identity_session.get({'user_id': user_id})
            
            # If no other identities exist, delete the user record
            if not remaining_identities:
                with users_repository.create_session() as user_session:
                    user_session.delete({'id': user_id})

def test_login_success():
    """Test successful login with valid credentials."""
    # Create a test user first
    test_username = 'auth_test_user_login'
    create_test_user(test_username)
    
    try:
        # Test login
        login_data = {
            'username': test_username,
            'password': 'testpassword'
        }
        response = execute_endpoint('/auth/login', method='POST', body=login_data)
        
        assert response['statusCode'] == 200
        assert response['body']['success'] is True
        assert 'token' in response['body']
        assert isinstance(response['body']['token'], str)
        assert len(response['body']['token']) > 0
    finally:
        # Cleanup
        delete_user(test_username)

def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    # Create a test user first
    test_username = 'auth_test_user_invalid'
    create_test_user(test_username)
    
    try:
        # Test login with wrong password
        login_data = {
            'username': test_username,
            'password': 'wrongpassword'
        }
        response = execute_endpoint('/auth/login', method='POST', body=login_data)
        
        assert response['statusCode'] == 400
        assert response['body']['success'] is False
        assert 'comment' in response['body']
    finally:
        # Cleanup
        delete_user(test_username)

def test_login_nonexistent_user():
    """Test login with non-existent user."""
    login_data = {
        'username': 'nonexistent_user',
        'password': 'somepassword'
    }
    response = execute_endpoint('/auth/login', method='POST', body=login_data)
    
    assert response['statusCode'] == 400
    assert response['body']['success'] is False
    assert 'comment' in response['body']

def test_verify_valid_token():
    """Test token verification with valid token."""
    # Create a test user first
    test_username = 'auth_test_user_verify'
    create_test_user(test_username)
    
    try:
        # Login to get a valid token
        login_data = {
            'username': test_username,
            'password': 'testpassword'
        }
        login_response = execute_endpoint('/auth/login', method='POST', body=login_data)
        token = login_response['body']['token']
        
        # Test token verification
        verify_data = {
            'token': token
        }
        response = execute_endpoint('/auth/verify', method='POST', body=verify_data)
        
        assert response['statusCode'] == 200
        assert response['body']['success'] is True
    finally:
        # Cleanup
        delete_user(test_username)

def test_verify_invalid_token():
    """Test token verification with invalid token."""
    verify_data = {
        'token': 'invalid_token_string'
    }
    response = execute_endpoint('/auth/verify', method='POST', body=verify_data)
    
    assert response['statusCode'] == 400
    assert response['body']['success'] is False
    assert response['body']['comment'] == 'VERIFY_FAILED'

def test_login_missing_username():
    """Test login with missing username."""
    login_data = {
        'password': 'testpassword'
    }
    response = execute_endpoint('/auth/login', method='POST', body=login_data)
    
    assert response['statusCode'] == 400
    assert response['body']['success'] is False
    assert 'comment' in response['body']

def test_login_missing_password():
    """Test login with missing password."""
    login_data = {
        'username': 'testuser'
    }
    response = execute_endpoint('/auth/login', method='POST', body=login_data)
    
    assert response['statusCode'] == 400
    assert response['body']['success'] is False
    assert 'comment' in response['body']

def test_verify_missing_token():
    """Test verify with missing token."""
    verify_data = {}
    response = execute_endpoint('/auth/verify', method='POST', body=verify_data)
    
    assert response['statusCode'] == 400
    assert response['body']['success'] is False
    assert 'comment' in response['body']
