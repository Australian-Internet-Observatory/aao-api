from base import execute_endpoint

def delete_user(username: str):
    """
    Delete a user by username.
    
    :param username: The username of the user to delete.
    :return: The response from the API call.
    """
    response = execute_endpoint(f'/users/{username}', method='DELETE', auth=True)
    return response

def create_test_user(username: str = 'testuser'):
    """
    Create a test user for testing purposes.
    
    :return: The response from the API call.
    """
    test_user = {
        'username': username,
        'password': 'testpassword',
        'full_name': 'Test User',
        'enabled': True,
        'role': 'user'
    }
    response = execute_endpoint('/users', method='POST', body=test_user, auth=True)
    return response

def get_user(username: str):
    """
    Get a user by username.
    
    :param username: The username of the user to retrieve.
    :return: The response from the API call.
    """
    response = execute_endpoint(f'/users/{username}', method='GET', auth=True)
    return response

def test_list_users():
    """Test listing all users via /users endpoint"""
    response = execute_endpoint('/users', method='GET', auth=True)
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
    body = response['body']
    assert isinstance(body, list), f"Expected list, got {type(body)}"
    for user in body:
        assert 'id' in user, "User ID is missing"
        assert 'username' in user, "Username is missing"
        assert 'full_name' in user, "Full name is missing"
        assert 'enabled' in user, "Enabled status is missing"
        assert 'role' in user, "Role is missing"

def test_get_users():
    response = execute_endpoint('/users', method='GET', auth=True)
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
    body = response['body']
    assert isinstance(body, list), f"Expected list, got {type(body)}"
    for user in body:
        assert 'id' in user, "User ID is missing"
        assert 'username' in user, "Username is missing"
        assert 'full_name' in user, "Full name is missing"
        assert 'enabled' in user, "Enabled status is missing"
        assert 'role' in user, "Role is missing"
        assert 'current_token' not in user, "Current token should not be present in the user list"
        
def test_create_new_user():
    username = 'testuser-create'
    response = create_test_user(username)
    assert response['statusCode'] == 201, f"Expected 201, got {response['statusCode']}"
    # Clean up
    delete_user(username)

def test_update_user():
    username = 'testuser-update'
    create_test_user(username)
    updated_user = {
        'username': username,
        'password': 'newpassword',
        'full_name': 'Updated Test User',
        'enabled': True,
        'role': 'admin'
    }
    execute_endpoint(f'/users/{username}', method='PATCH', body=updated_user, auth=True)
    user = get_user(username)
    assert user['statusCode'] == 200, f"Expected 200, got {user['statusCode']}"
    body = user['body']
    assert body['username'] == username, "Username did not match"
    assert body['full_name'] == 'Updated Test User', "Full name did not match"
    assert body['role'] == 'admin', "Role did not match"
    # Clean up
    delete_user(username)

# def test_get_current_user():
#     """Test getting the current user's information via /users/self endpoint"""
#     response = execute_endpoint('/users/self', method='GET', auth=True)
#     assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
#     body = response['body']
#     assert 'username' in body, "Username is missing"
#     assert 'full_name' in body, "Full name is missing"
#     assert 'enabled' in body, "Enabled status is missing"
#     assert 'role' in body, "Role is missing"
#     # Password should be present in the response for self
#     assert 'password' in body, "Password should be present for self endpoint"

def test_get_specific_user():
    """Test getting a specific user by username"""
    # First create a test user
    username = 'testuser-get'
    create_test_user(username)
    
    # Test getting the created user
    response = get_user(username)
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
    user = response['body']
    assert 'username' in user, "Username is missing"
    assert 'full_name' in user, "Full name is missing"
    assert 'enabled' in user, "Enabled status is missing"
    assert 'role' in user, "Role is missing"
    
    # Clean up
    delete_user(username)

def test_delete_user():
    """Test deleting a user"""
    # First create a test user
    username = 'testuser-delete'
    create_response = create_test_user(username)
    assert create_response['statusCode'] == 201, f"Failed to create test user: {create_response['statusCode']}"
    
    # Delete the user
    delete_response = delete_user(username)
    assert delete_response['statusCode'] == 200, f"Expected 200, got {delete_response['statusCode']}"
    body = delete_response['body']
    assert body['success'] == True, "Delete operation should be successful"
    assert 'deleted successfully' in body['comment'], "Success message should indicate deletion"
    
    # Verify user is deleted by trying to get it (should fail)
    get_response = get_user(username)
    assert get_response['statusCode'] == 400, f"Expected 400 for deleted user, got {get_response['statusCode']}"

def test_get_nonexistent_user():
    """Test getting a user that doesn't exist"""
    response = get_user('nonexistentuser')
    assert response['statusCode'] == 400, f"Expected 400, got {response['statusCode']}"
    body = response['body']
    assert body['success'] == False, "Should return failure for nonexistent user"
    assert 'not found' in body['comment'].lower(), "Error message should indicate user not found"

def test_delete_nonexistent_user():
    """Test deleting a user that doesn't exist"""
    response = delete_user('nonexistentuser')
    assert response['statusCode'] == 400, f"Expected 400, got {response['statusCode']}"
    body = response['body']
    assert body['success'] == False, "Should return failure for nonexistent user"
    assert 'not found' in body['comment'].lower(), "Error message should indicate user not found"

def test_create_duplicate_user():
    """Test creating a user that already exists"""
    # First create a test user
    username = 'testuser-duplicate'
    create_response = create_test_user(username)
    assert create_response['statusCode'] == 201, f"Failed to create test user: {create_response['statusCode']}"
    
    # Try to create the same user again
    duplicate_response = create_test_user(username)
    assert duplicate_response['statusCode'] == 400, f"Expected 400 for duplicate user, got {duplicate_response['statusCode']}"
    body = duplicate_response['body']
    assert body['success'] == False, "Should return failure for duplicate user"
    assert 'already exists' in body['comment'], "Error message should indicate user already exists"
    
    # Clean up
    delete_user(username)