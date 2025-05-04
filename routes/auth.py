from routes import route
from middlewares.authenticate import authenticate
from utils import Response, use, jwt
from configparser import ConfigParser
from utils.auth_providers import client as cilogon_client
from utils.security import sign_state_data, verify_signed_state_data

config = ConfigParser()
config.read('config.ini')

FRONTEND_URL = config['APP']['FRONTEND_URL']

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

@route('auth/cilogon/login', 'GET')
def cilogon_login(event, response: Response):
    """Initiates CILogon OIDC login flow."""
    """TODO: schema for the request and response"""
    try:
        # 1. Create authorization URL and state using Authlib
        authorization_endpoint = cilogon_client.metadata.get('authorization_endpoint')
       
        # If the metadata wasn't loaded correctly at startup, this is a server configuration issue
        if not authorization_endpoint:
             print("Error: CILogon authorization_endpoint not found in metadata. Check CILOGON_METADATA_URL.")
             return response.status(500).json({'success': False, 'comment': 'Server configuration error: CILogon metadata not loaded.'})

        uri, state = cilogon_client.create_authorization_url(authorization_endpoint)

        # 2. Prepare data to be stored in the cookie
        state_data_to_sign = {
            'state': state,
            'next_url': FRONTEND_URL
        }
        signed_state = sign_state_data(state_data_to_sign)

        # 3. Prepare cookie attributes
        # Max-Age is in seconds; Secure requires HTTPS; HttpOnly prevents JS access
        # SameSite=Lax is important for cross-site redirects
        cookie_attrs = [
            f"Max-Age={600}", # e.g., 10 minutes
            "Path=/",
            "HttpOnly",
            "Secure",
            "SameSite=Lax"
        ]
        cookie_string = f"cilogon_oauth_state={signed_state}; {'; '.join(cookie_attrs)}"

        # 4. Return 302 Redirect response with Set-Cookie header
        response.body = {
            'statusCode': 302,
            'headers': {
                'Location': uri,
                'Set-Cookie': cookie_string
            }
        }
        response.terminated = True
        return event, response, {}

    except Exception as e:
        print(f"CILogon login error: {e}")
        response.status(500).json({'success': False, 'comment': 'Login initiation failed'})
        return event, response, {}

# TODO: make path auth/cilogon/authorize
@route('callback', 'GET') # This path must match REDIRECT_URI in config.ini and CILogon setting
def cilogon_authorize(event, response: Response):
    """Handles the callback from CILogon after authentication."""
    """TODO: schema for the request and response"""
    try:
        # 1. Extract state from query params and cookie from headers
        query_params = event.get('queryStringParameters', {})
        returned_state = query_params.get('state')
        code = query_params.get('code') # Authorization code from CILogon

        headers = event.get('headers', {})
        cookie_header = headers.get('cookie') or headers.get('Cookie')
        signed_state_from_cookie = None
        if cookie_header:
            cookies = {c.split('=')[0].strip(): c.split('=', 1)[1].strip() for c in cookie_header.split(';') if '=' in c}
            signed_state_from_cookie = cookies.get('cilogon_oauth_state')

        # 2. Validate inputs
        if not returned_state or not code or not signed_state_from_cookie:
            response.status(400).json({'success': False, 'comment': 'Missing state, code, or cookie'})
            return event, response, {}

        # 3. Verify signed cookie data
        state_data = verify_signed_state_data(signed_state_from_cookie)
        if not state_data:
            response.status(400).json({'success': False, 'comment': 'Invalid or expired state cookie'})
            return event, response, {}

        # 4. Verify state parameter against cookie (CSRF check)
        original_state = state_data.get('state')
        next_url = state_data.get('next_url', '/') # Default redirect if missing

        if original_state != returned_state:
            response.status(400).json({'success': False, 'comment': 'State mismatch (CSRF suspected)'})
            return event, response, {}

        # --- State is valid ---

        # 5. Get user info (using OIDC userinfo endpoint)
        userinfo_endpoint = cilogon_client.metadata.get('userinfo_endpoint')
        userinfo = cilogon_client.get(userinfo_endpoint).json()
        # print("CILogon UserInfo:", userinfo)
        # --- You now have the authenticated user's details ---
        # Example: userinfo might contain 'sub', 'email', 'name', etc.

        # 6. TODO: Implement application logic:
        #    - Find or create a user based on CILogon ID

        # 7. Create a JWT token for our application
        app_user_data = {
            "username": userinfo.get('email', userinfo.get('sub')), # TODO: Example mapping - need to explore
            "full_name": userinfo.get('name', 'CILogon User'),
            "role": "user",
            "enabled": True,
            "cilogon_id": userinfo.get('sub'),
        }

        app_token, _ = jwt.create_token(app_user_data)

        # 8. Prepare final redirect response to the frontend
        #    Include app token in the redirect URL (e.g., fragment #token=...)
        final_redirect_url = f"{next_url}#token={app_token}"

        # Clear the temporary state cookie
        clear_cookie_attrs = [
            "Max-Age=0", # Expire immediately
            "Path=/",
            "HttpOnly",
            "Secure",
            "SameSite=Lax"
        ]
        clear_cookie_string = f"cilogon_oauth_state=deleted; {'; '.join(clear_cookie_attrs)}"

        response.body = {
            'statusCode': 302,
            'headers': {
                'Location': final_redirect_url,
                'Set-Cookie': clear_cookie_string
            }
        }
        response.terminated = True
        return event, response, {}

    except Exception as e:
        print(f"CILogon authorize error: {e}")
        # Log detailed error, including Authlib errors if possible
        # Consider redirecting to an error page on the frontend
        response.status(500).json({'success': False, 'comment': 'Authentication failed during callback'})
        return event, response, {}
