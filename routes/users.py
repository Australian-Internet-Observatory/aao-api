from routes import route
from middlewares.authenticate import authenticate, authorise
from utils import use, jwt
import hashlib
import boto3
import json

from configparser import ConfigParser
config = ConfigParser()
config.read('config.ini')

session = boto3.Session(
    aws_access_key_id=config['AWS']['ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS']['SECRET_ACCESS_KEY'],
    region_name='ap-southeast-2'
)

@route('users', 'GET')
@use(authenticate)
@use(authorise('admin'))
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
    s3 = session.client('s3')
    user_objects = s3.list_objects_v2(
        Bucket='fta-mobile-observations-holding-bucket',
        Prefix='metadata/dashboard-users/'
    )
    keys = [user['Key'] for user in user_objects['Contents'] if user['Key'].endswith('credentials.json')]
    users = []
    for key in keys:
        user_object = s3.get_object(
            Bucket='fta-mobile-observations-holding-bucket',
            Key=key
        )
        user_data = json.loads(user_object['Body'].read().decode('utf-8'))
        users.append(user_data)
    return users

@route('users', 'POST')
@use(authenticate)
@use(authorise('admin'))
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
                    type: object
                    properties:
                        username:
                            type: string
                            required: true
                        enabled:
                            type: boolean
                            required: true
                        password:
                            type: string
                            required: true
                        full_name:
                            type: string
                            required: true
                        role:
                            type: string
                            required: true
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
    s3 = session.client('s3')
    new_user = event['body']
    
    # Check if user already exists
    try:
        s3.head_object(
            Bucket='fta-mobile-observations-holding-bucket',
            Key=f'metadata/dashboard-users/{new_user["username"]}/credentials.json'
        )
        return response.status(400).json({
            "success": False,
            "comment": "User already exists"
        })
    except Exception as e:
        print(e)
    
    # Hash the password
    new_user['password'] = hashlib.md5(new_user['password'].encode('utf-8')).hexdigest()
    
    # Save the new user
    s3.put_object(
        Bucket='fta-mobile-observations-holding-bucket',
        Key=f'metadata/dashboard-users/{new_user["username"]}/credentials.json',
        Body=json.dumps(new_user).encode('utf-8')
    )
    
    return response.status(201).json({
        "success": True,
        "comment": "User created successfully"
    })

@route('users/{username}', 'PATCH')
@use(authenticate)
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
    if caller['username'] != event['pathParameters']['username'] and caller['role'] != 'admin':
        return response.status(403).json({
            "success": False,
            "comment": "UNAUTHORIZED"
        })
    
    s3 = session.client('s3')
    print(event)
    username = event['pathParameters']['username']
    user_object = None
    try:
        user_object = s3.get_object(
            Bucket='fta-mobile-observations-holding-bucket',
            Key=f'metadata/dashboard-users/{username}/credentials.json'
        )
    except Exception as e:
        return response.status(400).json({
            "success": False,
            "comment": "User not found"
        })
    old_data = json.loads(user_object['Body'].read().decode('utf-8'))
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
    if 'role' in new_data and caller['role'] != 'admin':
        return response.status(403).json({
            "success": False,
            "comment": "UNAUTHORIZED"
        })
    
    # If the password is being updated, hash it
    if 'password' in new_data:
        new_data['password'] = hashlib.md5(new_data['password'].encode('utf-8')).hexdigest()
    
    # Update the user data
    combined_data = {**old_data, **new_data}
    s3.put_object(
        Bucket='fta-mobile-observations-holding-bucket',
        Key=f'metadata/dashboard-users/{username}/credentials.json',
        Body=json.dumps(combined_data).encode('utf-8')
    )
    return {
        "success": True,
        "comment": "User updated successfully"
    }
    

@route('users/self', 'GET')
@use(authenticate)
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
    s3 = session.client('s3')
    user_object = None
    try:
        user_object = s3.get_object(
            Bucket='fta-mobile-observations-holding-bucket',
            Key=f'metadata/dashboard-users/{caller["username"]}/credentials.json'
        )
    except Exception as e:
        return response.status(400).json({
            "success": False,
            "comment": "User not found"
        })
    user_data = json.loads(user_object['Body'].read().decode('utf-8'))
    return user_data
    
@route('users/{username}', 'GET')
@use(authenticate)
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
    if caller['username'] != event['pathParameters']['username'] and caller['role'] != 'admin':
        return response.status(403).json({
            "success": False,
            "comment": "UNAUTHORIZED"
        })
    
    s3 = session.client('s3')
    username = event['pathParameters']['username']
    user_object = None
    try:
        user_object = s3.get_object(
            Bucket='fta-mobile-observations-holding-bucket',
            Key=f'metadata/dashboard-users/{username}/credentials.json'
        )
    except Exception as e:
        return response.status(400).json({
            "success": False,
            "comment": "User not found"
        })
    user_data = json.loads(user_object['Body'].read().decode('utf-8'))
    return user_data
