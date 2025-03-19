import json
import time
import hashlib
import base64
import utils.metadata_sub_bucket as metadata
from configparser import ConfigParser

class User:
    enabled: bool
    password: str
    username: str
    full_name: str

config = ConfigParser()
config.read('config.ini')

USERS_FOLDER_PREFIX = 'dashboard-users'
SESSION_FOLDER_PREFIX = 'guest-sessions'

def get_user_data(username: str) -> dict:
    """
    Retrieve user data from S3 based on the provided username.

    Args:
        username (str): The username of the user.

    Returns:
        dict: The user data as a dictionary, or None if an error occurs.
    """
    try:
        data = metadata.get_object(f'{USERS_FOLDER_PREFIX}/{username}/credentials.json').decode('utf-8')
        return json.loads(data)
    except Exception as e:
        print(e)
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
    # Copy all fields (except the password) from the user data to the payload
    copied_data = dict(user_data)
    if 'password' in copied_data:
        copied_data.pop('password')
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
    # Look up the session object in S3, depending if it is a user or guest session
    if 'role' in payload and payload['role'] == 'guest':
        session_object_path = f'{SESSION_FOLDER_PREFIX}/{payload["username"]}.json'
    else:
        session_object_path = f'{USERS_FOLDER_PREFIX}/{payload["username"]}/sessions/{exp}_{token}.json'
    
    try:
        metadata.get_object(session_object_path)
    except Exception as e:
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
    hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()
    if user_data is None or user_data['password'] != hashed_password:
        raise Exception("INVALID_CREDENTIALS")
    # Disable the most recent JSON web token for the user (delete the session object)
    # to prevent multiple logins
    most_recent_session_path = get_most_recent_session_path(username)
    if most_recent_session_path is not None:
        _, prev_token = most_recent_session_path.split('/')[-1].split('_')
        prev_token = '.'.join(prev_token.split('.')[:-1])
        disable_session_token(prev_token)
    token, payload = create_token(user_data)
    # Save the token to the user's session (for verification later)
    exp = payload['exp']
    session_object_path = f'{USERS_FOLDER_PREFIX}/{username}/sessions/{exp}_{token}.json'
    metadata.put_object(session_object_path, json.dumps(payload).encode('utf-8'))
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
        return None
    header_base64, payload_base64, signature = parts
    payload = json.loads(base64.b64decode(payload_base64).decode('utf-8'))
    # Find the user data from the payload
    username = payload['username']
    user_data = get_user_data(username)
    if user_data is None:
        return None
    token, payload = create_token(user_data)
    # Save the token to the user's session (for verification later)
    exp = payload['exp']
    session_object_path = f'{USERS_FOLDER_PREFIX}/{username}/sessions/{exp}_{token}.json'
    metadata.put_object(session_object_path, json.dumps(payload).encode('utf-8'))
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
    exp = payload['exp']
    session_object_path = f'{USERS_FOLDER_PREFIX}/{payload["username"]}/sessions/{exp}_{token}.json'
    try:
        metadata.delete_object(session_object_path)
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
    sessions = metadata.list_objects(f'{USERS_FOLDER_PREFIX}/{username}/sessions/')
    for session in sessions:
        try:
            metadata.delete_object(session)
        except Exception as e:
            return False
    return True

def get_most_recent_session_path(username: str) -> dict:
    """
    Retrieve the path of the most recent session for the given username.

    Args:
        username (str): The username of the user.

    Returns:
        dict: The path of the most recent session, or None if no sessions exist.
    """
    user_data = get_user_data(username)
    if user_data is None:
        return None
    sessions = metadata.list_objects(f'{USERS_FOLDER_PREFIX}/{username}/sessions/')
    if not sessions:
        return None
    most_recent_session = sessions[0]
    for session in sessions:
        session_data = metadata.head_object(session)
        most_recent_session_data = metadata.head_object(most_recent_session)
        if session_data['LastModified'] > most_recent_session_data['LastModified']:
            most_recent_session = session
    return most_recent_session

if __name__ == "__main__":
    token = create_session_token('dantran', 'dantran')
    # print(token)
    # print(verify_token(token))
    # print(get_most_recent_session_path('dantran'))