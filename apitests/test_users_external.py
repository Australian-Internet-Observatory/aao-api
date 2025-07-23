from base import execute_endpoint
from db.shared_repositories import users_repository, user_identities_repository
from uuid import uuid4
import time


def create_test_external_user(provider: str = 'cilogon', provider_user_id: str = None, full_name: str = 'Test External User'):
    """
    Create a test external user directly in the database for testing purposes.
    
    :param provider: The identity provider (default: 'cilogon')
    :param provider_user_id: The provider user ID (default: generated UUID)
    :param full_name: The full name of the user
    :return: The user_id of the created user
    """
    if provider_user_id is None:
        provider_user_id = f"test-{provider}-{str(uuid4())}"
    
    # Create user in users table
    user_data = {
        'full_name': full_name,
        'enabled': False,  # External users start disabled
        'role': 'user'
    }
    
    with users_repository.create_session() as user_session:
        user_entity = user_session.create(user_data)
        user_id = user_entity['id']  # Extract the ID from the returned entity
    
    # Create identity in user_identities table
    identity_data = {
        'user_id': user_id,
        'provider': provider,
        'provider_user_id': provider_user_id,
        'password': None,  # External users don't have passwords
        'created_at': int(time.time())
    }
    
    with user_identities_repository.create_session() as identity_session:
        identity_session.create(identity_data)
    
    return user_id


def delete_test_external_user(user_id: str):
    """
    Delete a test external user from the database.
    
    :param user_id: The user ID to delete
    """
    with user_identities_repository.create_session() as identity_session:
        # Delete all identities for this user
        user_identities = identity_session.list()
        for identity in user_identities:
            if identity.user_id == user_id:
                identity_session.delete({
                    'user_id': identity.user_id,
                    'provider': identity.provider
                })
    
    with users_repository.create_session() as user_session:
        user_session.delete({'id': user_id})


def test_list_external_users():
    """Test listing all external users via /users/external endpoint"""
    # Create a test external user
    test_user_id = create_test_external_user()
    
    try:
        response = execute_endpoint('/users/external', method='GET', auth=True)
        assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
        body = response['body']
        assert isinstance(body, list), f"Expected list, got {type(body)}"
        
        # Check if our test user is in the list
        test_user_found = False
        for user in body:
            assert 'id' in user, "User ID is missing"
            assert 'provider' in user, "Provider is missing"
            assert 'provider_user_id' in user, "Provider user ID is missing"
            assert 'full_name' in user, "Full name is missing"
            assert 'enabled' in user, "Enabled status is missing"
            assert 'role' in user, "Role is missing"
            assert 'created_at' in user, "Created at timestamp is missing"
            
            if user['id'] == test_user_id:
                test_user_found = True
                assert user['provider'] == 'cilogon', "Expected cilogon provider"
                assert user['enabled'] == False, "External user should start disabled"
        
        assert test_user_found, "Test external user not found in list"
        
    finally:
        # Clean up
        delete_test_external_user(test_user_id)


def test_get_external_user():
    """Test getting a specific external user via /users/external/{user_id} endpoint"""
    # Create a test external user
    test_user_id = create_test_external_user(full_name="Test Get External User")
    
    try:
        response = execute_endpoint(f'/users/external/{test_user_id}', method='GET', auth=True)
        assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
        body = response['body']
        
        assert body['id'] == test_user_id, "User ID mismatch"
        assert body['provider'] == 'cilogon', "Expected cilogon provider"
        assert body['full_name'] == "Test Get External User", "Full name mismatch"
        assert body['enabled'] == False, "External user should start disabled"
        assert body['role'] == 'user', "Role mismatch"
        assert 'created_at' in body, "Created at timestamp is missing"
        
    finally:
        # Clean up
        delete_test_external_user(test_user_id)


def test_get_external_user_not_found():
    """Test getting a non-existent external user"""
    fake_user_id = str(uuid4())
    response = execute_endpoint(f'/users/external/{fake_user_id}', method='GET', auth=True)
    assert response['statusCode'] == 400, f"Expected 400, got {response['statusCode']}"
    body = response['body']
    assert body['success'] == False, "Expected success to be False"
    assert 'User not found' in body['comment'], "Expected 'User not found' in comment"


def test_enable_external_user():
    """Test enabling an external user via /users/external/{user_id}/enable endpoint"""
    # Create a test external user (starts disabled)
    test_user_id = create_test_external_user(full_name="Test Enable External User")
    
    try:
        # Enable the user
        response = execute_endpoint(f'/users/external/{test_user_id}/enable', method='POST', auth=True)
        assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
        body = response['body']
        assert body['success'] == True, "Expected success to be True"
        assert 'enabled successfully' in body['comment'], "Expected success message"
        
        # Verify the user is now enabled
        verify_response = execute_endpoint(f'/users/external/{test_user_id}', method='GET', auth=True)
        assert verify_response['statusCode'] == 200, "Failed to get user after enabling"
        verify_body = verify_response['body']
        assert verify_body['enabled'] == True, "User should be enabled"
        
    finally:
        # Clean up
        delete_test_external_user(test_user_id)


def test_disable_external_user():
    """Test disabling an external user via /users/external/{user_id}/disable endpoint"""
    # Create a test external user and enable it first
    test_user_id = create_test_external_user(full_name="Test Disable External User")
    
    # First enable it
    with users_repository.create_session() as user_session:
        user = user_session.get_first({'id': test_user_id})
        user.enabled = True
        user_session.update(user)
    
    try:
        # Disable the user
        response = execute_endpoint(f'/users/external/{test_user_id}/disable', method='POST', auth=True)
        assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
        body = response['body']
        assert body['success'] == True, "Expected success to be True"
        assert 'disabled successfully' in body['comment'], "Expected success message"
        
        # Verify the user is now disabled
        verify_response = execute_endpoint(f'/users/external/{test_user_id}', method='GET', auth=True)
        assert verify_response['statusCode'] == 200, "Failed to get user after disabling"
        verify_body = verify_response['body']
        assert verify_body['enabled'] == False, "User should be disabled"
        
    finally:
        # Clean up
        delete_test_external_user(test_user_id)


def test_delete_external_user():
    """Test deleting an external user via /users/external/{user_id} endpoint"""
    # Create a test external user
    test_user_id = create_test_external_user(full_name="Test Delete External User")
    
    # Delete the user via API
    response = execute_endpoint(f'/users/external/{test_user_id}', method='DELETE', auth=True)
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
    body = response['body']
    assert body['success'] == True, "Expected success to be True"
    assert 'deleted successfully' in body['comment'], "Expected success message"
    
    # Verify the user is gone
    verify_response = execute_endpoint(f'/users/external/{test_user_id}', method='GET', auth=True)
    assert verify_response['statusCode'] == 400, "User should not exist after deletion"


def test_external_user_operations_on_local_user():
    """Test that external user operations fail on local users"""
    # Create a local user (user with local identity)
    from apitests.test_users import create_test_user, delete_user
    
    local_username = f"testlocal-{str(uuid4())[:8]}"
    create_response = create_test_user(local_username)
    assert create_response['statusCode'] == 201, "Failed to create test local user"
    
    try:
        # Get the user ID of the local user
        get_response = execute_endpoint(f'/users/{local_username}', method='GET', auth=True)
        assert get_response['statusCode'] == 200, "Failed to get local user"
        local_user_id = get_response['body']['id']
        
        # Try to get it as an external user (should fail)
        response = execute_endpoint(f'/users/external/{local_user_id}', method='GET', auth=True)
        assert response['statusCode'] == 400, "Should not be able to get local user as external"
        assert 'not an external user' in response['body']['comment'], "Expected 'not an external user' message"
        
        # Try to enable it as an external user (should fail)
        response = execute_endpoint(f'/users/external/{local_user_id}/enable', method='POST', auth=True)
        assert response['statusCode'] == 400, "Should not be able to enable local user as external"
        assert 'not an external user' in response['body']['comment'], "Expected 'not an external user' message"
        
        # Try to delete it as an external user (should fail)
        response = execute_endpoint(f'/users/external/{local_user_id}', method='DELETE', auth=True)
        assert response['statusCode'] == 400, "Should not be able to delete local user as external"
        assert 'not an external user' in response['body']['comment'], "Expected 'not an external user' message"
        
    finally:
        # Clean up local user
        delete_user(local_username)


def test_unauthorized_access():
    """Test that non-admin users cannot access external user endpoints"""
    # This test would require creating a non-admin user and testing with their credentials
    # For now, we'll test with no authentication
    
    response = execute_endpoint('/users/external', method='GET', auth=False)
    assert response['statusCode'] == 401, f"Expected 401 for unauthenticated request, got {response['statusCode']}"