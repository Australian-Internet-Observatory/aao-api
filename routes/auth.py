from routes import route
from middlewares.authenticate import authenticate
from utils import Response, use, jwt

@route('auth/login', 'POST')
def login(event, response: Response):
    """Log the user in and return a JSON web token.
    
    Log the user in and create a JSON web token for the user, which can be used to authenticate the user in future requests.
    ---
    tags:
        - auth
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        username:
                            type: string
                        password:
                            type: string
    responses:
        200:
            description: A successful login
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                            token:
                                type: string
        400:
            description: A failed login
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
    """
    username = event['body']['username']
    password = event['body']['password']
    try:
        return {
            'success': True,
            'token': jwt.create_session_token(username, password)
        }
    except Exception as e:
        return response.status(400).json({
            'success': False,
            'comment': str(e)
        })

@route('auth/verify', 'POST')
def verify(event, response: Response):
    """Verify the JSON web token.
    
    Return whether the JSON web token is valid.
    ---
    tags:
        - auth
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        token:
                            type: string
    responses:
        200:
            description: A successful verification
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
        400:
            description: A failed verification
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
                                example: 'VERIFY_FAILED'
    """
    token = event['body']['token']
    if jwt.verify_token(token):
        return {
            'success': True
        }
    return response.status(400).json({
        'success': False,
        'comment': 'VERIFY_FAILED'
    })

@route('auth/logout', 'POST')
def logout(event, response: Response):
    """Log the user out.
    
    Log the user out and disable the JSON web token to prevent further authentication using the same token.
    ---
    tags:
        - auth
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        token:
                            type: string
    responses:
        200:
            description: A successful logout
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
        400:
            description: A failed logout
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
                                example: 'LOGOUT_FAILED'
    """
    token = event['body']['token']
    if jwt.disable_session_token(token):
        return {
            'success': True
        }
    return response.status(400).json({
        'success': False,
        'comment': 'LOGOUT_FAILED'
    })
    
@route('auth/refresh', 'POST')
def refresh(event, response: Response):
    """Refresh the JSON web token.
    
    Refresh the JSON web token to extend the session.
    ---
    tags:
        - auth
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        token:
                            type: string
    responses:
        200:
            description: A successful refresh
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                            token:
                                type: string
        400:
            description: A failed refresh
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
                                example: 'REFRESH_FAILED'
    """
    token = event['body']['token']
    try:
        return {
            'success': True,
            'token': jwt.refresh_session_token(token)
        }
    except Exception as e:
        return response.status(400).json({
            'success': False,
            'comment': str(e)
        })