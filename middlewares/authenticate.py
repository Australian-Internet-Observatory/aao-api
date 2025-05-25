import boto3
from configparser import ConfigParser
from utils import jwt

config = ConfigParser()
config.read('config.ini')

session_us_east = boto3.Session(
    region_name='us-east-2',
    aws_access_key_id=config['AWS']['ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS']['SECRET_ACCESS_KEY']
)

def validate_session_token(arg_session_token):
    return jwt.verify_token(arg_session_token)

def authenticate(event, response, context):
    """Middleware to authenticate the user using a JSON web token.
    
    This function passes the payload of the JSON web token to the applied function.
    
    Appends the following OpenAPI documentation to the applied function:
    
    ---
    security:
        - bearerAuth: []
    """
    headers = event['headers']
    if headers is None:
        response.status(401).json({
            "success": False,
            "comment": f'NO_HEADERS',
        })
        return event, response, context
    bearer = headers.get('Authorization', None)
    if bearer is None:
        response.status(401).json({
            "success": False,
            "comment": f'NO_AUTHORIZATION_HEADER',
        })
        return event, response, context
    if not bearer.startswith('Bearer '):
        response.status(401).json({
            "success": False,
            "comment": f'INVALID_AUTHORIZATION_HEADER',
        })
        return event, response, context
    session_token = bearer[7:]
    if not validate_session_token(session_token):
        response.status(401).json({
            "success": False,
            "comment": "SESSION_TOKEN_EXPIRED",
        })
        return event, response, context
    event['user'] = jwt.decode_token(session_token)
    print(f"[Authentication] User successfully verified: {event['user']}")
    return event, response, context