from models.user import User, UserIdentity, UserORM
from routes import route
from middlewares.authorise import Role, authorise
from middlewares.authenticate import authenticate
from utils import use
from urllib.parse import unquote
from db.shared_repositories import users_repository, user_identities_repository

def get_external_user_dict(user: User, external_identity: UserIdentity):
    """Helper function to convert external user entity to a dictionary."""
    return {
        "id": user.id,
        "provider": external_identity.provider,
        "provider_user_id": external_identity.provider_user_id,
        "enabled": user.enabled,
        "full_name": user.full_name,
        "role": user.role,
        "created_at": external_identity.created_at,
        "email": user.primary_email
    }


@route('users/external', 'GET')
@use(authenticate)
@use(authorise(Role.ADMIN))
def list_external_users(event):
    """Returns a list of external users from the database (admin only)

    Returns a list of external users (users whose only identity is from CILogon) stored in the database.
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
                                provider:
                                    type: string
                                    example: cilogon
                                provider_user_id:
                                    type: string
                                enabled:
                                    type: boolean
                                full_name:
                                    type: string
                                role:
                                    type: string
                                email:
                                    type: string
                                created_at:
                                    type: integer
                                    description: Unix timestamp
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
        
        # Get all external identities (non-local providers)
        all_identities = identity_session.list()
        external_identities = [i for i in all_identities if i.provider != 'local']
        
        external_users = []
        for identity in external_identities:
            # Check if this user has ONLY external identities (no local identity)
            user_identities = [i for i in all_identities if i.user_id == identity.user_id]
            
            # Only include users who don't have any local identities
            has_local_identity = any(i.provider == 'local' for i in user_identities)
            if not has_local_identity:
                user = user_session.get_first({'id': identity.user_id})
                if user:
                    external_users.append(get_external_user_dict(user, identity))
        
    return external_users


@route('users/external/{user_id}/enable', 'POST')
@use(authenticate)
@use(authorise(Role.ADMIN))
def enable_external_user(event, response):
    """Enable an external user (admin only)

    Enable an external user to allow them access to the API.
    ---
    tags:
        - users
    parameters:
        - in: path
          name: user_id
          required: true
          schema:
              type: string
          description: The ID of the external user to enable
    responses:
        200:
            description: User enabled successfully
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
            description: User not found or operation failed
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
                                example: 'User not found or not an external user'
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
    user_id = unquote(user_id)
    
    with users_repository.create_session() as user_session, \
         user_identities_repository.create_session() as identity_session:
        
        # Verify user exists
        user = user_session.get_first({'id': user_id})
        if not user:
            return response.status(400).json({
                "success": False,
                "comment": "User not found"
            })
        
        # Verify this is an external user (has no local identity)
        user_identities = identity_session.get({
            'user_id': user_id
        })
        has_local_identity = any(i.provider == 'local' for i in user_identities)
        if has_local_identity:
            return response.status(400).json({
                "success": False,
                "comment": "User is not an external user"
            })
        
        # Enable the user
        user.enabled = True
        user_session.update(user)
    
    return {
        "success": True,
        "comment": "External user enabled successfully"
    }


@route('users/external/{user_id}/disable', 'POST')
@use(authenticate)
@use(authorise(Role.ADMIN))
def disable_external_user(event, response):
    """Disable an external user (admin only)

    Disable an external user to revoke their access to the API.
    ---
    tags:
        - users
    parameters:
        - in: path
          name: user_id
          required: true
          schema:
              type: string
          description: The ID of the external user to disable
    responses:
        200:
            description: User disabled successfully
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
            description: User not found or operation failed
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
                                example: 'User not found or not an external user'
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
    user_id = unquote(user_id)
    
    with users_repository.create_session() as user_session, \
         user_identities_repository.create_session() as identity_session:
        
        # Verify user exists
        user = user_session.get_first({'id': user_id})
        if not user:
            return response.status(400).json({
                "success": False,
                "comment": "User not found"
            })
        
        # Verify this is an external user (has no local identity)
        user_identities = identity_session.get({
            'user_id': user_id
        })
        has_local_identity = any(i.provider == 'local' for i in user_identities)
        if has_local_identity:
            return response.status(400).json({
                "success": False,
                "comment": "User is not an external user"
            })
        
        # Disable the user
        user.enabled = False
        user_session.update(user)
    
    return {
        "success": True,
        "comment": "External user disabled successfully"
    }


@route('users/external/{user_id}', 'DELETE')
@use(authenticate)
@use(authorise(Role.ADMIN))
def delete_external_user(event, response):
    """Delete an external user (admin only)

    Delete an external user from both users and user_identities tables.
    ---
    tags:
        - users
    parameters:
        - in: path
          name: user_id
          required: true
          schema:
              type: string
          description: The ID of the external user to delete
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
            description: User not found or operation failed
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
                                example: 'User not found or not an external user'
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
    user_id = unquote(user_id)
    
    with users_repository.create_session() as user_session, \
         user_identities_repository.create_session() as identity_session:
        
        # Verify user exists
        user = user_session.get_first({'id': user_id})
        if not user:
            return response.status(400).json({
                "success": False,
                "comment": "User not found"
            })
        
        # Verify this is an external user (has no local identity)
        user_identities = identity_session.get({
            'user_id': user_id
        })
        has_local_identity = any(i.provider == 'local' for i in user_identities)
        if has_local_identity:
            return response.status(400).json({
                "success": False,
                "comment": "User is not an external user"
            })
        
        # Delete all user identities first (foreign key constraint)
        for identity in user_identities:
            identity_session.delete({
                'user_id': identity.user_id,
                'provider': identity.provider
            })
        
        # Delete the user
        user_session.delete({'id': user_id})
    
    return {
        "success": True,
        "comment": "External user deleted successfully"
    }


@route('users/external/{user_id}', 'GET')
@use(authenticate)
@use(authorise(Role.ADMIN))
def get_external_user(event, response):
    """Get an external user from the database (admin only)

    Get an external user's information stored in the database.
    ---
    tags:
        - users
    parameters:
        - in: path
          name: user_id
          required: true
          schema:
              type: string
          description: The ID of the external user to get
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
                            provider:
                                type: string
                                example: cilogon
                            provider_user_id:
                                type: string
                            enabled:
                                type: boolean
                            full_name:
                                type: string
                            role:
                                type: string
                            created_at:
                                type: integer
                                description: Unix timestamp
        400:
            description: User not found or operation failed
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
                                example: 'User not found or not an external user'
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
    user_id = unquote(user_id)
    
    with users_repository.create_session() as user_session, \
         user_identities_repository.create_session() as identity_session:
        
        # Verify user exists
        user = user_session.get_first({'id': user_id})
        if not user:
            return response.status(400).json({
                "success": False,
                "comment": "User not found"
            })
        
        # Get user identities and verify this is an external user
        user_identities = identity_session.get({
            'user_id': user_id
        })
        
        has_local_identity = any(i.provider == 'local' for i in user_identities)
        if has_local_identity:
            return response.status(400).json({
                "success": False,
                "comment": "User is not an external user"
            })
        
        # Get the external identity (should be only one for external users)
        external_identity = next(
            (i for i in user_identities if i.provider != 'local'), 
            None
        )
        
        if not external_identity:
            return response.status(400).json({
                "success": False,
                "comment": "No external identity found for user"
            })
        
        return get_external_user_dict(user, external_identity)