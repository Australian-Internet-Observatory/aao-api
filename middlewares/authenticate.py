import boto3
from configparser import ConfigParser
from utils import jwt
from db.shared_repositories import users_repository

config = ConfigParser()
config.read('config.ini')

session_us_east = boto3.Session(
    region_name='us-east-2',
    aws_access_key_id=config['AWS']['ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS']['SECRET_ACCESS_KEY']
)

def is_user_exists(user_id: str) -> bool:
    with users_repository.create_session() as session:
        user = session.get_first({
            'id': user_id
        })
        return user is not None

def authenticate(event, response, context):
    """Middleware to authenticate the user using a JSON web token.
    
    This function passes the payload of the JSON web token to the applied function.
    
    Appends the following OpenAPI documentation to the applied function:
    
    ---
    security:
        - bearerAuth: []
    """
    headers = event.get('headers', None)
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
    token = bearer[7:]
    if not jwt.verify_token(token):
        response.status(401).json({
            "success": False,
            "comment": "SESSION_TOKEN_EXPIRED",
        })
        return event, response, context
    
    json_web_token = jwt.JsonWebToken.from_token(token)
    
    # Ensure the user exists in the database
    if not is_user_exists(json_web_token.user.id):
        response.status(401).json({
            "success": False,
            "comment": "USER_NOT_FOUND",
        })
        return event, response, context
    
    event['identity'] = json_web_token.identity
    event['user'] = json_web_token.user
    print(f"[Authentication] User successfully verified: {event['user']} with identity {event['identity']}")
    return event, response, context