from models.user import User, UserIdentity, UserORM
from routes import route
from middlewares.authorise import Role, authorise
from middlewares.authenticate import authenticate
from utils import use
from utils.hash_password import hash_password
from urllib.parse import unquote
import time
from db.shared_repositories import users_repository, user_identities_repository

from config import config


def get_user_dict(user: User, identity: UserIdentity=None):
    """Helper function to convert user entity to a dictionary."""
    return {
        "id": user.id,
        "username": identity.provider_user_id if identity else None,
        "enabled": user.enabled,
        "full_name": user.full_name,
        "role": user.role,
        "provider": identity.provider if identity else None,
    }

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
                                id:
                                    type: string
                                username:
                                    type: string
                                enabled:
                                    type: boolean
                                full_name:
                                    type: string
                                role:
                                    type: string
                                provider:
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
    with users_repository.create_session() as user_session, \
         user_identities_repository.create_session() as identity_session:
        
        user_entities = user_session.list()
        users = []
        
        for user in user_entities:
            # Get local identity for username
            local_identity = identity_session.get_first({
                'user_id': user.id, 
            })
            users.append(get_user_dict(user, local_identity))
        
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
    new_user_data = event['body']
    username = new_user_data['username']
    password = new_user_data['password']
    
    # Check if user already exists by username
    with user_identities_repository.create_session() as identity_session:
        existing_identity = identity_session.get_first({
            'provider': 'local', 
            'provider_user_id': username
        })
        if existing_identity is not None:
            return response.status(400).json({
                "success": False,
                "comment": "User already exists"
            })
    
    # Create user in users table
    with users_repository.create_session() as user_session:
        user_data = {
            'full_name': new_user_data['full_name'],
            'enabled': new_user_data['enabled'],
            'role': new_user_data['role']
        }
        user_entity = user_session.create(user_data)
        user_id = user_entity['id']
    
    # Create identity in user_identities table
    with user_identities_repository.create_session() as identity_session:
        identity_data = {
            'user_id': user_id,
            'provider': 'local',
            'provider_user_id': username,
            'password': hash_password(password),
            'created_at': int(time.time())
        }
        identity_session.create(identity_data)
    
    return response.status(201).json({
        "success": True,
        "comment": "User created successfully"
    })

@route('users/{user_id}/role', 'PATCH')
@use(authenticate)
@use(authorise(Role.ADMIN))
def change_user_role(event, response):
    """Change a user's role (admin only)

    Change the role of a user in the database.
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
                        role:
                            type: string
    responses:
        200:
            description: Role changed successfully
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
            description: Role change failed
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
    user_id = event['pathParameters']['user_id']
    new_role = event['body']['role']
    
    # Check if user exists by ID
    with users_repository.create_session() as user_session:
        user_entity = user_session.get_first({'id': user_id})
        if user_entity is None:
            return response.status(400).json({
                "success": False,
                "comment": "User not found"
            })
        
        # Update user's role in users table
        user_session.update({'id': user_id, 'role': new_role})
    
    return response.status(200).json({
        "success": True,
        "comment": "User role changed successfully"
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
    caller: User = event['user']
    
    username = event['pathParameters']['username']
    # Decode the URL-encoded username
    username = unquote(username)
    
    # Find user identity by username
    with user_identities_repository.create_session() as identity_session:
        user_identity = identity_session.get_first({
            'provider': 'local',
            'provider_user_id': username
        })
        
        if user_identity is None:
            return response.status(400).json({
                "success": False,
                "comment": "User not found"
            })
        
        user_id = user_identity.user_id
    
    # Only editable by self, or admin
    if caller.id != user_id and Role.parse(caller.role) != Role.ADMIN:
        return response.status(403).json({
            "success": False,
            "comment": "UNAUTHORIZED"
        })
    
    new_data = event['body']
    acceptable_fields = ['enabled', 'password', 'full_name', 'role']
    
    # Ensure that the fields are acceptable
    for key in new_data:
        if key not in acceptable_fields:
            return response.status(400).json({
                "success": False,
                "comment": f"Field '{key}' is not acceptable"
            })
    
    # Ensure the role is only updated by an admin
    if 'role' in new_data and Role.parse(caller.role) != Role.ADMIN:
        return response.status(403).json({
            "success": False,
            "comment": "UNAUTHORIZED"
        })
    
    # Update user fields in users table
    user_fields = {k: v for k, v in new_data.items() if k in ['enabled', 'full_name', 'role']}
    if user_fields:
        with users_repository.create_session() as user_session:
            user_entity = user_session.get_first({'id': user_id})
            if user_entity is None:
                return response.status(400).json({
                    "success": False,
                    "comment": "User not found"
                })
            
            old_data = user_entity.model_dump()
            combined_data = {**old_data, **user_fields}
            user_session.update(combined_data)
    
    # Update password in user_identities table
    if 'password' in new_data:
        with user_identities_repository.create_session() as identity_session:
            identity_data = user_identity.model_dump()
            identity_data['password'] = hash_password(new_data['password'])
            identity_session.update(identity_data)
    
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
                            id:
                                type: string
                            username:
                                type: string
                            enabled:
                                type: boolean
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
        caller: User = event['user']
        
        # Get local identity for username
        with user_identities_repository.create_session() as identity_session:
            local_identity = identity_session.get_first({
                'user_id': caller.id,
                'provider': 'local'
            })
        
        return get_user_dict(caller, local_identity)
        
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
    responses:
        200:
            description: A successful response
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            id:
                                type: string
                            username:
                                type: string
                            enabled:
                                type: boolean
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
    
    # Find user identity by username
    with user_identities_repository.create_session() as identity_session:
        user_identity = identity_session.get_first({
            'provider': 'local',
            'provider_user_id': username
        })
        
        if user_identity is None:
            return response.status(400).json({
                "success": False,
                "comment": "User not found"
            })
        
        user_id = user_identity.user_id
    
    # Check authorization
    if caller.id != user_id and Role.parse(caller.role) != Role.ADMIN:
        return response.status(403).json({
            "success": False,
            "comment": "UNAUTHORIZED"
        })
    
    try:
        with users_repository.create_session() as user_session, \
             user_identities_repository.create_session() as identity_session:
            user_entity = user_session.get_first({'id': user_id})
            if user_entity is None:
                raise Exception("User not found")
            
            user_identity = identity_session.get_first({
                'user_id': user_id,
                'provider': 'local'
            })
            
            return get_user_dict(user_entity, user_identity)
            
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

    Delete a user by removing their data from the database.
    ---
    tags:
        - users
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
    
    # Find user identity by username
    with user_identities_repository.create_session() as identity_session:
        user_identity = identity_session.get_first({
            'provider': 'local',
            'provider_user_id': username
        })
        
        if user_identity is None:
            return response.status(400).json({
                "success": False,
                "comment": "User not found"
            })
        
        user_id = user_identity.user_id
        
        # Delete the identity record
        try:
            identity_session.delete({
                'user_id': user_id,
                'provider': 'local'
            })
        except Exception as e:
            return response.status(400).json({
                "success": False,
                "comment": "User not found"
            })
    
    # Check if user has other identities
    with user_identities_repository.create_session() as identity_session:
        remaining_identities = identity_session.get({'user_id': user_id})
        
        # If no other identities exist, delete the user record
        if not remaining_identities:
            try:
                with users_repository.create_session() as user_session:
                    user_session.delete({'id': user_id})
            except Exception as e:
                return response.status(400).json({
                    "success": False,
                    "comment": "Failed to delete user record"
                })
    
    return response.status(200).json({
        "success": True,
        "comment": f"User {username} deleted successfully"
    })
