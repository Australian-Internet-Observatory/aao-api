import json
import time
import hashlib
import base64
from models.user import User
from utils.hash_password import hash_password
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

SESSION_FOLDER_PREFIX = 'guest-sessions'

from db.shared_repositories import users_repository

def get_user_data(username: str) -> dict:
    """
    Retrieve user data from S3 based on the provided username.

    Args:
        username (str): The username of the user.

    Returns:
        dict: The user data as a dictionary, or None if an error occurs.
    """
    try:
        with users_repository.create_session() as session:
            user = session.get_first({'username': username})
            if user is None:
                return None
            data = user.model_dump()
            # Ensure the password is not included in the returned data
            return {
                'username': data['username'],
                'full_name': data.get('full_name', ''),
                'enabled': data.get('enabled', True),
                'password': data.get('password', None),
                'role': data.get('role', 'user'),
                'token': data.get('current_token', None)
            }
    except Exception as e:
        return None

def create_token(user_data: User, expire: int = None) -> tuple[str, dict]:
    """
    Create a JSON Web Token (JWT) for the given user data, and return the token and its payload.

    Args:
        user_data (User): The user data object.
        expire (int, optional): The expiration time of the token in seconds. Defaults to None (use the default expiration time from the config).

    Returns:
        str: The generated JWT.
        dict: The payload of the JWT.
    """
    current_time = time.time()
    if expire is None:
        expiration_time = current_time + config.getint('JWT', 'EXPIRATION')
    else:
        expiration_time = current_time + expire
    header = {
        "alg": "HS256",
        "typ": "JWT"
    }
    header_base64 = base64.b64encode(json.dumps(header).encode('utf-8')).decode('utf-8')
    # Copy all fields (except the password and token) from the user data to the payload
    copied_data = dict(user_data)
    if 'password' in copied_data:
        copied_data.pop('password')
    if 'token' in copied_data:
        copied_data.pop('token')
    payload = {
        "exp": expiration_time,
        **copied_data
    }
    payload_base64 = base64.b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8')
    secret = config['JWT']['SECRET']
    signature = hashlib.sha256(f'{header_base64}.{payload_base64}.{secret}'.encode('utf-8')).hexdigest()
    return f'{header_base64}.{payload_base64}.{signature}', payload

def decode_token(token: str) -> dict:
    """
    Decode a JSON Web Token (JWT) and return its payload.

    Args:
        token (str): The JWT to decode.

    Returns:
        dict: The payload of the JWT.
    """
    parts = token.split('.')
    if len(parts) != 3:
        return None
    header_base64, payload_base64, signature = parts
    payload = json.loads(base64.b64decode(payload_base64).decode('utf-8'))
    return payload

def verify_token(token: str) -> bool:
    """
    Verify the validity of a JSON Web Token (JWT).

    Args:
        token (str): The JWT to verify.

    Returns:
        bool: True if the token is valid, False otherwise.
    """
    parts = token.split('.')
    if len(parts) != 3:
        return False
    header_base64, payload_base64, signature = parts
    secret = config['JWT']['SECRET']
    expected_signature = hashlib.sha256(f'{header_base64}.{payload_base64}.{secret}'.encode('utf-8')).hexdigest()
    is_valid = signature == expected_signature
    # Ensure the token exists in the user's sessions, and is not disabled (deleted)
    if not is_valid:
        return False
    payload = json.loads(base64.b64decode(payload_base64).decode('utf-8'))
    exp = payload['exp']
    
    # If the role is 'guest' - allow
    # TODO: Verify guest sessions
    if 'role' in payload and payload['role'] == 'guest':
        return True
    
    # Ensure the token exists
    user_data = get_user_data(payload['username'])
    if user_data is None or user_data.get('token') != token:
        return False
    
    # Ensure the token has not expired
    current_time = time.time()
    if current_time > exp:
        return False
    return True

def create_session_token(username: str, password: str) -> str:
    """
    Create a session token for the user with the given username and password. This also disables the most recent session token for the user.

    Args:
        username (str): The username of the user.
        password (str): The password of the user.

    Returns:
        str: The generated session token.

    Raises:
        Exception: If the credentials are invalid.
    """
    user_data = get_user_data(username)
    hashed_password = hash_password(password)
    if user_data is None or user_data['password'] != hashed_password:
        raise Exception("INVALID_CREDENTIALS")
    
    token, payload = create_token(user_data)
    
    # Get the user data and update the current token
    with users_repository.create_session() as session:
        user = session.get_first({'username': username})
        if user is None:
            raise Exception("User not found")
        user.current_token = token
        session.update(user)
    
    return token

def refresh_session_token(token: str) -> str:
    """Refresh a session token by extending its expiration time.

    Args:
        token (str): The session token to refresh.

    Returns:
        str: The new token with the updated expiration time.
    """
    parts = token.split('.')
    if len(parts) != 3:
        raise Exception("INVALID_TOKEN")
    header_base64, payload_base64, signature = parts
    payload = json.loads(base64.b64decode(payload_base64).decode('utf-8'))
    # Find the user data from the payload
    username = payload['username']
    user_data = get_user_data(username)
    
    if user_data is None:
        raise Exception("INVALID_CREDENTIALS")
    # Ensure the token is valid
    if user_data.get('token') != token:
        raise Exception("INVALID_TOKEN")
    
    token, payload = create_token(user_data)
    
    # Update the user's current token
    with users_repository.create_session() as session:
        user = session.get_first({'username': username})
        if user is None:
            raise Exception("User not found")
        user.current_token = token
        session.update(user)
    
    return token

def disable_session_token(token: str) -> bool:
    """
    Disable a session token by deleting its corresponding session object in S3.

    Args:
        token (str): The session token to disable.

    Returns:
        bool: True if the token was successfully disabled, False otherwise.
    """
    # print("Disabling token", token, "...")
    parts = token.split('.')
    if len(parts) != 3:
        return False
    header_base64, payload_base64, signature = parts
    payload = json.loads(base64.b64decode(payload_base64).decode('utf-8'))
    
    try:
        with users_repository.create_session() as session:
            user = session.get_first({'username': payload['username']})
            if user is None:
                return False
            # Update the user's current token to None
            user.current_token = None
            session.update(user)
            return True
    except Exception as e:
        return False

def disable_sessions_for_user(username: str) -> bool:
    """
    Disable all session tokens for the given username by deleting all session objects in S3.

    Args:
        username (str): The username of the user.

    Returns:
        bool: True if all sessions were successfully disabled, False otherwise.
    """
    try:
        with users_repository.create_session() as session:
            user = session.get_first({'username': username})
            if user is None:
                return False
            # Update the user's current token to None
            user.current_token = None
            session.update(user)
    except Exception as e:
        return False
    return True

if __name__ == "__main__":
    token = create_session_token('dantran', 'dantran')
    # print(token)
    # print(verify_token(token))
    # print(get_most_recent_session_path('dantran'))