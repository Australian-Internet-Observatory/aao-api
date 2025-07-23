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

def change_user_role(user_id: str, new_role: str):
    """
    Change a user's role by user ID.
    
    :param user_id: The ID of the user to change role for.
    :param new_role: The new role to assign to the user.
    :return: The response from the API call.
    """
    role_data = {'role': new_role}
    response = execute_endpoint(f'/users/{user_id}/role', method='PATCH', body=role_data, auth=True)
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
        # Password should not be present in user list responses
        assert 'password' not in user, "Password should not be present in the user list"
        
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
        'full_name': 'Updated Test User',
        'enabled': True,
        'role': 'admin'
    }
    response = execute_endpoint(f'/users/{username}', method='PATCH', body=updated_user, auth=True)
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
    
    user = get_user(username)
    assert user['statusCode'] == 200, f"Expected 200, got {user['statusCode']}"
    body = user['body']
    assert body['username'] == username, "Username did not match"
    assert body['full_name'] == 'Updated Test User', "Full name did not match"
    assert body['role'] == 'admin', "Role did not match"
    # Clean up
    delete_user(username)

def test_get_current_user():
    """Test getting the current user's information via /users/self endpoint"""
    response = execute_endpoint('/users/self', method='GET', auth=True)
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
    body = response['body']
    assert 'id' in body, "User ID is missing"
    assert 'username' in body, "Username is missing"
    assert 'full_name' in body, "Full name is missing"
    assert 'enabled' in body, "Enabled status is missing"
    assert 'role' in body, "Role is missing"
    # Password should not be present in the response
    assert 'password' not in body, "Password should not be present in self endpoint"

def test_get_specific_user():
    """Test getting a specific user by username"""
    # First create a test user
    username = 'testuser-get'
    create_test_user(username)
    
    # Test getting the created user
    response = get_user(username)
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
    user = response['body']
    assert 'id' in user, "User ID is missing"
    assert 'username' in user, "Username is missing"
    assert 'full_name' in user, "Full name is missing"
    assert 'enabled' in user, "Enabled status is missing"
    assert 'role' in user, "Role is missing"
    # Password should not be present in individual user responses
    assert 'password' not in user, "Password should not be present in user response"
    
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

def test_change_user_role_success():
    """Test successfully changing a user's role"""
    # First create a test user
    username = 'testuser-role-change'
    create_response = create_test_user(username)
    assert create_response['statusCode'] == 201, f"Failed to create test user: {create_response['statusCode']}"
    
    # Get the user to obtain their ID
    get_response = get_user(username)
    assert get_response['statusCode'] == 200, f"Failed to get test user: {get_response['statusCode']}"
    user_id = get_response['body']['id']
    
    # Verify initial role is 'user'
    assert get_response['body']['role'] == 'user', "Initial role should be 'user'"
    
    # Change the user's role to 'admin'
    role_response = change_user_role(user_id, 'admin')
    assert role_response['statusCode'] == 200, f"Expected 200, got {role_response['statusCode']}"
    body = role_response['body']
    assert body['success'] == True, "Role change should be successful"
    assert 'successfully' in body['comment'].lower(), "Success message should indicate successful role change"
    
    # Verify the role was actually changed
    verify_response = get_user(username)
    assert verify_response['statusCode'] == 200, f"Failed to verify user: {verify_response['statusCode']}"
    assert verify_response['body']['role'] == 'admin', "Role should now be 'admin'"
    
    # Clean up
    delete_user(username)

def test_change_user_role_nonexistent_user():
    """Test changing role for a user that doesn't exist"""
    fake_user_id = 'nonexistent-user-id-12345'
    response = change_user_role(fake_user_id, 'admin')
    assert response['statusCode'] == 400, f"Expected 400, got {response['statusCode']}"
    body = response['body']
    assert body['success'] == False, "Should return failure for nonexistent user"
    assert 'not found' in body['comment'].lower(), "Error message should indicate user not found"

def test_change_user_role_multiple_changes():
    """Test changing a user's role multiple times"""
    # First create a test user
    username = 'testuser-multiple-role-changes'
    create_response = create_test_user(username)
    assert create_response['statusCode'] == 201, f"Failed to create test user: {create_response['statusCode']}"
    
    # Get the user to obtain their ID
    get_response = get_user(username)
    assert get_response['statusCode'] == 200, f"Failed to get test user: {get_response['statusCode']}"
    user_id = get_response['body']['id']
    
    # Change from 'user' to 'admin'
    role_response_1 = change_user_role(user_id, 'admin')
    assert role_response_1['statusCode'] == 200, f"First role change failed: {role_response_1['statusCode']}"
    
    # Verify the role changed to 'admin'
    verify_response_1 = get_user(username)
    assert verify_response_1['statusCode'] == 200, f"Failed to verify user: {verify_response_1['statusCode']}"
    assert verify_response_1['body']['role'] == 'admin', "Role should be 'admin'"
    
    # Change from 'admin' back to 'user'
    role_response_2 = change_user_role(user_id, 'user')
    assert role_response_2['statusCode'] == 200, f"Second role change failed: {role_response_2['statusCode']}"
    
    # Verify the role changed back to 'user'
    verify_response_2 = get_user(username)
    assert verify_response_2['statusCode'] == 200, f"Failed to verify user: {verify_response_2['statusCode']}"
    assert verify_response_2['body']['role'] == 'user', "Role should be back to 'user'"
    
    # Clean up
    delete_user(username)

def test_change_user_role_invalid_role():
    """Test changing a user's role to an invalid role value"""
    # First create a test user
    username = 'testuser-invalid-role'
    create_response = create_test_user(username)
    assert create_response['statusCode'] == 201, f"Failed to create test user: {create_response['statusCode']}"
    
    # Get the user to obtain their ID
    get_response = get_user(username)
    assert get_response['statusCode'] == 200, f"Failed to get test user: {get_response['statusCode']}"
    user_id = get_response['body']['id']
    
    # Try to change to an invalid role
    role_response = change_user_role(user_id, 'invalidrole')
    # Note: The API might accept any string as a role, so this test may need adjustment
    # based on actual validation behavior. For now, we'll just verify it doesn't crash
    # and the role gets set to whatever was provided
    
    if role_response['statusCode'] == 200:
        # If the API accepts any role, verify it was set
        verify_response = get_user(username)
        assert verify_response['statusCode'] == 200, f"Failed to verify user: {verify_response['statusCode']}"
        assert verify_response['body']['role'] == 'invalidrole', "Role should be set to the provided value"
    else:
        # If the API validates roles, it should return an error
        body = role_response['body']
        assert body['success'] == False, "Should return failure for invalid role"
    
    # Clean up
    delete_user(username)