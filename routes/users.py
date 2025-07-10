from routes import route
from middlewares.authorise import Role, authorise
from middlewares.authenticate import authenticate
from utils import use
from utils.hash_password import hash_password
from urllib.parse import unquote

from configparser import ConfigParser
config = ConfigParser()
config.read('config.ini')

from db.shared_repositories import users_repository

@route('users', 'GET')
@use(authenticate)
@use(authorise(Role.USER, Role.ADMIN))
# Event is not directly used here, but is needed for authenticate to work
def list_users(event): 
    """Returns a list of users from the database (admin only)

    Returns a list of users stored in the database.
    ---
    tags:
        - users

    responses:
        200:
            description: A successful response
            content:
                application/json:
                    schema:
                        type: array
                        items:
                            type: object
                            properties:
                                username:
                                    type: string
                                enabled:
                                    type: boolean
                                password:
                                    type: string
                                full_name:
                                    type: string
                                role:
                                    type: string
        400:
            description: A failed response
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                                example: False
                            comment:
                                type: string
        403:
            description: Unauthorized access
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                                example: False
                            comment:
                                type: string
                                example: 'UNAUTHORISED'
    """
    def get_user_dict(user):
        """Helper function to convert user entity to a dictionary."""
        return {
            "id": user.id,
            "username": user.username,
            "enabled": user.enabled,
            "full_name": user.full_name,
            "role": user.role,
        }
    
    with users_repository.create_session() as session:
        user_entities = session.list()
        users = [get_user_dict(user) for user in user_entities]
    return users

@route('users', 'POST')
@use(authenticate)
@use(authorise(Role.ADMIN))
def create_user(event, response):
    """Create a new user (admin only)

    Create a new user in the database.
    ---
    tags:
        - users
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    required:
                        - username
                        - enabled
                        - password
                        - full_name
                        - role
                    type: object
                    properties:
                        username:
                            type: string
                        enabled:
                            type: boolean
                        password:
                            type: string
                        full_name:
                            type: string
                        role:
                            type: string
    responses:
        201:
            description: User created successfully
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                            comment:
                                type: string
        400:
            description: User creation failed
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                                example: False
                            comment:
                                type: string
                                example: 'User already exists'
        403:
            description: Unauthorized access
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                                example: False
                            comment:
                                type: string
                                example: 'UNAUTHORISED'
    """
    new_user = event['body']
    
    # Check if user already exists
    with users_repository.create_session() as session:
        if session.get_first({'username': new_user['username']}) is not None:
            return response.status(400).json({
                "success": False,
                "comment": "User already exists"
            })
        
        # Hash the password
        new_user['password'] = hash_password(new_user['password'])
        
        # Save the new user
        session.create(new_user)
    
    return response.status(201).json({
        "success": True,
        "comment": "User created successfully"
    })

@route('users/{username}', 'PATCH')
@use(authenticate)
@use(authorise(Role.USER, Role.ADMIN))
def edit_user(event, response):
    """Edit a user's information (self or admin only)

    Edit a user's information. All fields are optional, and only the fields provided will be updated.
    ---
    tags:
        - users
    parameters:
        - in: path
          name: username
          required: true
          schema:
              type: string
          description: The username of the user to edit
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        enabled:
                            type: boolean
                        password:
                            type: string
                        full_name:
                            type: string
                        role:
                            type: string
    responses:
        200:
            description: A successful edit
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                            comment:
                                type: string
        400:
            description: A failed edit
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                                example: False
                            comment:
                                type: string
                                example: 'User not found'
        403:
            description: Unauthorized edit
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                                example: False
                            comment:
                                type: string
                                example: 'UNAUTHORISED'
    """
    caller = event['user']
    
    username = event['pathParameters']['username']
    # Decode the URL-encoded username
    username = unquote(username)
    
    # Only editable by self, or admin
    if caller['username'] != username and Role.parse(caller['role']) != Role.ADMIN:
        return response.status(403).json({
            "success": False,
            "comment": "UNAUTHORIZED"
        })
    
    with users_repository.create_session() as session:
        user_entity = session.get_first({'username': username})
        if user_entity is None:
            return response.status(400).json({
                "success": False,
                "comment": "User not found"
            })
        
        old_data = user_entity.model_dump()
        new_data = event['body']
        new_data.pop('username', None)
        
        acceptable_fields = ['enabled', 'password', 'full_name', 'role']
        
        # Ensure that the fields are acceptable
        for key in new_data:
            if key not in acceptable_fields:
                return response.status(400).json({
                    "success": False,
                    "comment": f"Field '{key}' is not acceptable"
                })
        
        # Ensure the role is only updated by an admin
        if 'role' in new_data and Role.parse(caller['role']) != Role.ADMIN:
            return response.status(403).json({
                "success": False,
                "comment": "UNAUTHORIZED"
            })
        
        # If the password is being updated, hash it
        if 'password' in new_data:
            new_data['password'] = hash_password(new_data['password'])
        
        # Update the user data
        combined_data = {**old_data, **new_data}
        session.update(combined_data)
        return {
            "success": True,
            "comment": "User updated successfully"
        }

@route('users/self', 'GET')
@use(authenticate)
@use(authorise(Role.USER, Role.ADMIN))
def get_current_user(event, response):
    """Get the current user's information

    Get the information of the user making the request.
    ---
    tags:
        - users
    responses:
        200:
            description: A successful response
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            username:
                                type: string
                            enabled:
                                type: boolean
                            password:
                                type: string
                            full_name:
                                type: string
                            role:
                                type: string
        400:
            description: A failed response
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                                example: False
                            comment:
                                type: string
                                example: 'User not found'
    """
    try:
        with users_repository.create_session() as session:
            user_entity = session.get_first({'username': event['user']['username']})
            if user_entity is None:
                raise Exception("User not found")
            user_data = user_entity.model_dump()
            return user_data
    except Exception as e:
        return response.status(400).json({
            "success": False,
            "comment": "User not found"
        })
    
@route('users/{username}', 'GET')
@use(authenticate)
@use(authorise(Role.USER, Role.ADMIN))
def get_user(event, response):
    """Get a user from the database (self or admin only)

    Get a user's information stored in the database.
    ---
    tags:
        - users
    parameters:
        - in: path
          name: username
          required: true
          schema:
              type: string
          description: The username of the user to get
    responses:
        200:
            description: A successful response
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            username:
                                type: string
                            enabled:
                                type: boolean
                            password:
                                type: string
                            full_name:
                                type: string
                            role:
                                type: string
        400:
            description: A failed response
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                                example: False
                            comment:
                                type: string
                                example: 'User not found'
        403:
            description: Unauthorized access
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                                example: False
                            comment:
                                type: string
                                example: 'UNAUTHORISED'
    """
    
    # Only admin or self can view
    caller = event['user']
    username = event['pathParameters']['username']
    # Decode the URL-encoded username
    username = unquote(username)
    
    if caller['username'] != username and Role.parse(caller['role']) != Role.ADMIN:
        return response.status(403).json({
            "success": False,
            "comment": "UNAUTHORIZED"
        })
    
    try:
        with users_repository.create_session() as session:
            user_entity = session.get_first({'username': username})
            if user_entity is None:
                raise Exception("User not found")
            user_data = user_entity.model_dump()
            return user_data
    except Exception as e:
        return response.status(400).json({
            "success": False,
            "comment": "User not found"
        })

@route('users/{username}', 'DELETE')
@use(authenticate)
@use(authorise(Role.ADMIN))
def delete_user(event, response):
    """Delete a user (admin only)

    Delete a user by moving their data to the recycle bin.
    ---
    tags:
        - users
    parameters:
        - in: path
          name: username
          required: true
          schema:
              type: string
          description: The username of the user to delete
    responses:
        200:
            description: User deleted successfully
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                            comment:
                                type: string
        400:
            description: User deletion failed
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                                example: False
                            comment:
                                type: string
                                example: 'User not found'
        403:
            description: Unauthorized access
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                                example: False
                            comment:
                                type: string
                                example: 'UNAUTHORISED'
    """
    username = event['pathParameters']['username']
    # Decode the URL-encoded username
    username = unquote(username)
    
    try:
        with users_repository.create_session() as session:
            session.delete({'username': username})
    except Exception as e:
        return response.status(400).json({
            "success": False,
            "comment": "User not found"
        })
    
    return response.status(200).json({
        "success": True,
        "comment": f"User {username} deleted successfully"
    })
