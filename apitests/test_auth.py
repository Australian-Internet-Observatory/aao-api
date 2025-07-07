from base import execute_endpoint
from utils.hash_password import hash_password

# Need to access the database directly as without functional authentication, it is not possible to create users through the API (which needs authentication).
from db.shared_repositories import users_repository

def create_test_user(username: str = 'testuser'):
    """
    Create a test user for testing purposes.
    
    :return: The response from the API call.
    """
    test_user = {
        'username': username,
        'password': hash_password('testpassword'),
        'full_name': 'Test User',
        'enabled': True,
        'role': 'user'
    }
    with users_repository.create_session() as session:
        session.create(test_user)

def delete_user(username: str):
    """
    Delete a user by username.
    
    :param username: The username of the user to delete.
    :return: The response from the API call.
    """
    with users_repository.create_session() as session:
        session.delete({'username': username})

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

def test_logout_valid_token():
    """Test logout with valid token."""
    # Create a test user first
    test_username = 'auth_test_user_logout'
    create_test_user(test_username)
    
    try:
        # Login to get a valid token
        login_data = {
            'username': test_username,
            'password': 'testpassword'
        }
        login_response = execute_endpoint('/auth/login', method='POST', body=login_data)
        token = login_response['body']['token']
        
        # Test logout
        logout_data = {
            'token': token
        }
        response = execute_endpoint('/auth/logout', method='POST', body=logout_data)
        
        assert response['statusCode'] == 200
        assert response['body']['success'] is True
        
        # Verify the token is no longer valid after logout
        verify_data = {
            'token': token
        }
        verify_response = execute_endpoint('/auth/verify', method='POST', body=verify_data)
        assert verify_response['statusCode'] == 400
        assert verify_response['body']['success'] is False
    finally:
        # Cleanup
        delete_user(test_username)

def test_logout_invalid_token():
    """Test logout with invalid token."""
    logout_data = {
        'token': 'invalid_token_string'
    }
    response = execute_endpoint('/auth/logout', method='POST', body=logout_data)
    
    assert response['statusCode'] == 400
    assert response['body']['success'] is False
    assert response['body']['comment'] == 'LOGOUT_FAILED'

def test_refresh_valid_token():
    """Test token refresh with valid token."""
    # Create a test user first
    test_username = 'auth_test_user_refresh'
    create_test_user(test_username)
    
    try:
        # Login to get a valid token
        login_data = {
            'username': test_username,
            'password': 'testpassword'
        }
        login_response = execute_endpoint('/auth/login', method='POST', body=login_data)
        original_token = login_response['body']['token']
        
        # Test token refresh
        refresh_data = {
            'token': original_token
        }
        response = execute_endpoint('/auth/refresh', method='POST', body=refresh_data)
        
        assert response['statusCode'] == 200
        assert response['body']['success'] is True
        assert 'token' in response['body']
        assert isinstance(response['body']['token'], str)
        assert len(response['body']['token']) > 0
        
        # Verify the new token is valid
        verify_data = {
            'token': response['body']['token']
        }
        verify_response = execute_endpoint('/auth/verify', method='POST', body=verify_data)
        assert verify_response['statusCode'] == 200
        assert verify_response['body']['success'] is True
    finally:
        # Cleanup
        delete_user(test_username)

def test_refresh_invalid_token():
    """Test token refresh with invalid token."""
    refresh_data = {
        'token': 'invalid_token_string'
    }
    response = execute_endpoint('/auth/refresh', method='POST', body=refresh_data)
    
    assert response['statusCode'] == 400
    assert response['body']['success'] is False
    assert 'comment' in response['body']

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

def test_logout_missing_token():
    """Test logout with missing token."""
    logout_data = {}
    response = execute_endpoint('/auth/logout', method='POST', body=logout_data)
    
    assert response['statusCode'] == 400
    assert response['body']['success'] is False
    assert 'comment' in response['body']

def test_refresh_missing_token():
    """Test refresh with missing token."""
    refresh_data = {}
    response = execute_endpoint('/auth/refresh', method='POST', body=refresh_data)
    
    assert response['statusCode'] == 400
    assert response['body']['success'] is False
    assert 'comment' in response['body']
