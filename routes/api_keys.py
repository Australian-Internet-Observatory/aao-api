"""
API Key management endpoints.

This module provides CRUD operations for API keys, allowing users to:
- Create new API keys
- List their own API keys (or all keys for admins)
- Get details of specific API keys
- Delete (revoke) API keys
"""

import time
from routes import route
from middlewares.authorise import Role, authorise
from middlewares.authenticate import authenticate
from utils import use
from models.user import User
from models.api_key import ApiKey, ApiKeyCreate, ApiKeyWithSecret
from utils.api_key import (
    generate_api_key,
    get_api_key_by_id,
    get_user_api_keys,
    delete_api_key
)
from db.shared_repositories import api_keys_repository


@route('api-keys', 'POST')
@use(authenticate)
@use(authorise(Role.USER, Role.ADMIN))
def create_api_key(event, response):
    """Create a new API key for the authenticated user
    
    Create a new API key. The full key is only shown once in the response.
    ---
    tags:
        - api-keys
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    required:
                        - title
                    properties:
                        title:
                            type: string
                            description: A descriptive title for the API key
                            example: "Data Export Script"
                        description:
                            type: string
                            description: Optional description of the key's purpose
                            example: "API key for automated data export pipeline"
    responses:
        201:
            description: API key created successfully
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                                example: true
                            api_key:
                                type: object
                                properties:
                                    id:
                                        type: string
                                    user_id:
                                        type: string
                                    title:
                                        type: string
                                    description:
                                        type: string
                                    suffix:
                                        type: string
                                        description: Last 6 characters of the key
                                    key:
                                        type: string
                                        description: The full API key (only shown once)
                                    created_at:
                                        type: integer
                            warning:
                                type: string
                                example: "Store this key securely. It will not be shown again."
        400:
            description: Invalid request
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                                example: false
                            comment:
                                type: string
        401:
            description: Not authenticated
        403:
            description: Insufficient permissions
    """
    caller: User = event['user']
    body = event['body']
    
    # Validate required fields
    if 'title' not in body:
        return response.status(400).json({
            "success": False,
            "comment": "MISSING_TITLE"
        })
    
    # Generate API key
    full_key, hashed_key, suffix = generate_api_key()
    
    # Create API key record
    api_key_data = {
        'user_id': caller.id,
        'title': body['title'],
        'description': body.get('description'),
        'hashed_key': hashed_key,
        'suffix': suffix,
        'created_at': int(time.time()),
        'last_used_at': None
    }
    
    with api_keys_repository.create_session() as session:
        created_key = session.create(api_key_data)
    
    # Return the full key (only time it's shown)
    return response.status(201).json({
        "success": True,
        "api_key": {
            "id": created_key['id'],
            "user_id": created_key['user_id'],
            "title": created_key['title'],
            "description": created_key['description'],
            "suffix": created_key['suffix'],
            "key": full_key,  # Only shown once!
            "created_at": created_key['created_at']
        },
        "warning": "Store this key securely. It will not be shown again."
    })


@route('api-keys', 'GET')
@use(authenticate)
@use(authorise(Role.USER, Role.ADMIN))
def list_api_keys(event, response):
    """List API keys for the authenticated user (or any user for admins)
    
    List all API keys. Regular users see only their own keys.
    Admins can view any user's keys by providing a user_id query parameter.
    ---
    tags:
        - api-keys
    parameters:
        - in: query
          name: user_id
          schema:
              type: string
          required: false
          description: User ID to list keys for (admin only)
    responses:
        200:
            description: List of API keys
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            api_keys:
                                type: array
                                items:
                                    type: object
                                    properties:
                                        id:
                                            type: string
                                        user_id:
                                            type: string
                                        title:
                                            type: string
                                        description:
                                            type: string
                                        suffix:
                                            type: string
                                            description: Last 6 characters of the key
                                        created_at:
                                            type: integer
                                        last_used_at:
                                            type: integer
        401:
            description: Not authenticated
        403:
            description: Insufficient permissions
    """
    caller: User = event['user']
    query_params = event.get('queryStringParameters', {}) or {}
    
    # Check if admin is querying for another user's keys
    target_user_id = query_params.get('user_id')
    
    if target_user_id and target_user_id != caller.id:
        # Only admins can view other users' keys
        if Role.parse(caller.role) != Role.ADMIN:
            return response.status(403).json({
                "success": False,
                "comment": "UNAUTHORIZED"
            })
        user_id = target_user_id
    else:
        user_id = caller.id
    
    # Get API keys for the user
    api_keys = get_user_api_keys(user_id)
    
    # Convert to dict and remove hashed_key
    api_keys_data = [
        {
            "id": key.id,
            "user_id": key.user_id,
            "title": key.title,
            "description": key.description,
            "suffix": key.suffix,
            "created_at": key.created_at,
            "last_used_at": key.last_used_at
        }
        for key in api_keys
    ]
    
    return response.status(200).json({
        "api_keys": api_keys_data
    })


@route('api-keys/{key_id}', 'GET')
@use(authenticate)
@use(authorise(Role.USER, Role.ADMIN))
def get_api_key(event, response):
    """Get details of a specific API key
    
    Get the details of an API key. Regular users can only view their own keys.
    ---
    tags:
        - api-keys
    parameters:
        - in: path
          name: key_id
          schema:
              type: string
          required: true
          description: API key ID
    responses:
        200:
            description: API key details
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            id:
                                type: string
                            user_id:
                                type: string
                            title:
                                type: string
                            description:
                                type: string
                            suffix:
                                type: string
                            created_at:
                                type: integer
                            last_used_at:
                                type: integer
        401:
            description: Not authenticated
        403:
            description: Key belongs to another user
        404:
            description: Key not found
    """
    caller: User = event['user']
    key_id = event['pathParameters']['key_id']
    
    # Get the API key
    api_key = get_api_key_by_id(key_id)
    
    if api_key is None:
        return response.status(404).json({
            "success": False,
            "comment": "API_KEY_NOT_FOUND"
        })
    
    # Check authorization (user can only view their own keys, unless admin)
    if api_key.user_id != caller.id and Role.parse(caller.role) != Role.ADMIN:
        return response.status(403).json({
            "success": False,
            "comment": "UNAUTHORIZED"
        })
    
    return response.status(200).json({
        "id": api_key.id,
        "user_id": api_key.user_id,
        "title": api_key.title,
        "description": api_key.description,
        "suffix": api_key.suffix,
        "created_at": api_key.created_at,
        "last_used_at": api_key.last_used_at
    })


@route('api-keys/{key_id}', 'DELETE')
@use(authenticate)
@use(authorise(Role.USER, Role.ADMIN))
def delete_api_key_route(event, response):
    """Delete (revoke) an API key
    
    Delete an API key, immediately revoking its access. Regular users can only delete their own keys.
    ---
    tags:
        - api-keys
    parameters:
        - in: path
          name: key_id
          schema:
              type: string
          required: true
          description: API key ID to delete
    responses:
        200:
            description: API key deleted successfully
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                                example: true
                            comment:
                                type: string
                                example: "API key deleted successfully"
        401:
            description: Not authenticated
        403:
            description: Key belongs to another user
        404:
            description: Key not found
    """
    caller: User = event['user']
    key_id = event['pathParameters']['key_id']
    
    # Get the API key to check ownership
    api_key = get_api_key_by_id(key_id)
    
    if api_key is None:
        return response.status(404).json({
            "success": False,
            "comment": "API_KEY_NOT_FOUND"
        })
    
    # Check authorization (user can only delete their own keys, unless admin)
    if api_key.user_id != caller.id and Role.parse(caller.role) != Role.ADMIN:
        return response.status(403).json({
            "success": False,
            "comment": "UNAUTHORIZED"
        })
    
    # Delete the API key
    success = delete_api_key(key_id)
    
    if success:
        return response.status(200).json({
            "success": True,
            "comment": "API key deleted successfully"
        })
    else:
        return response.status(500).json({
            "success": False,
            "comment": "FAILED_TO_DELETE_KEY"
        })
