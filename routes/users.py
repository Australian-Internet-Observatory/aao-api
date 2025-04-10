from datetime import datetime
from routes import route
from middlewares.authorise import Role, authorise
from middlewares.authenticate import authenticate
from utils import use, jwt
import hashlib
import boto3
import json
import utils.metadata_sub_bucket as metadata

from configparser import ConfigParser
config = ConfigParser()
config.read('config.ini')

session = boto3.Session(
    aws_access_key_id=config['AWS']['ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS']['SECRET_ACCESS_KEY'],
    region_name='ap-southeast-2'
)

USERS_FOLDER_PREFIX = 'dashboard-users'

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
    user_keys = metadata.list_objects(f'{USERS_FOLDER_PREFIX}/')
    keys = [key for key in user_keys if key.endswith('credentials.json')]
    users = []
    for key in keys:
        user_data = json.loads(metadata.get_object(key).decode('utf-8'))
        users.append(user_data)
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
    user_path = f'{USERS_FOLDER_PREFIX}/{new_user["username"]}/credentials.json'
    
    # Check if user already exists
    try:
        metadata.head_object(user_path)
        return response.status(400).json({
            "success": False,
            "comment": "User already exists"
        })
    except Exception as e:
        print(e)
    
    # Hash the password
    new_user['password'] = hashlib.md5(new_user['password'].encode('utf-8')).hexdigest()
    
    # Save the new user
    metadata.put_object(user_path, json.dumps(new_user).encode('utf-8'))
    
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
    # Only editable by self, or admin
    if caller['username'] != event['pathParameters']['username'] and Role.parse(caller['role']) != Role.ADMIN:
        return response.status(403).json({
            "success": False,
            "comment": "UNAUTHORIZED"
        })
    
    username = event['pathParameters']['username']
    user_path = f'{USERS_FOLDER_PREFIX}/{username}/credentials.json'
    try:
        old_data = json.loads(metadata.get_object(user_path).decode('utf-8'))
    except Exception as e:
        return response.status(400).json({
            "success": False,
            "comment": "User not found"
        })
    
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
        new_data['password'] = hashlib.md5(new_data['password'].encode('utf-8')).hexdigest()
    
    # Update the user data
    combined_data = {**old_data, **new_data}
    metadata.put_object(user_path, json.dumps(combined_data).encode('utf-8'))
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
    caller = event['user']
    user_path = f'{USERS_FOLDER_PREFIX}/{caller["username"]}/credentials.json'
    try:
        user_data = json.loads(metadata.get_object(user_path).decode('utf-8'))
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
    if caller['username'] != event['pathParameters']['username'] and Role.parse(caller['role']) != Role.ADMIN:
        return response.status(403).json({
            "success": False,
            "comment": "UNAUTHORIZED"
        })
    
    username = event['pathParameters']['username']
    user_path = f'{USERS_FOLDER_PREFIX}/{username}/credentials.json'
    try:
        user_data = json.loads(metadata.get_object(user_path).decode('utf-8'))
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
    user_path = f'{USERS_FOLDER_PREFIX}/{username}/credentials.json'
    try:
        metadata.delete_object(user_path)
    except Exception as e:
        print(e)
        return response.status(400).json({
            "success": False,
            "comment": "User not found"
        })
    
    return response.status(200).json({
        "success": True,
        "comment": "User deleted successfully"
    })
