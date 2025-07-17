from dataclasses import dataclass
import json
import time
import hashlib
import base64
import uuid
from models.user import User, UserIdentity, UserIdentityORM, UserORM
from utils.hash_password import hash_password
from configparser import ConfigParser
from db.shared_repositories import users_repository, user_identities_repository

config = ConfigParser()
config.read("config.ini")

JWT_SECRET = config["JWT"]["SECRET"]

def to_base64(data: dict) -> str:
    """
    Convert a dictionary to a base64 encoded string.
    
    Args:
        data (dict): The dictionary to encode.
        
    Returns:
        str: Base64 encoded string of the JSON representation of the dictionary.
    """
    return base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8")

@dataclass
class JsonWebToken:
    """
    Class to handle JSON Web Token (JWT) creation, decoding, and verification.
    """
    sub: str  # subject identifier (user ID)
    iat: int  # issued at timestamp
    exp: int  # expiration timestamp
    role: str  # user role
    full_name: str  # user's full name
    enabled: bool  # whether the user is enabled
    provider: str | None = None  # identity provider (e.g., 'local', 'cilogon', None for guest)
    
    @property
    def payload(self) -> dict:
        """
        Convert the JsonWebToken instance to a dictionary payload.
        
        Returns:
            dict: The JWT payload.
        """
        return {
            "sub": self.sub,
            "iat": self.iat,
            "exp": self.exp,
            "role": self.role,
            "full_name": self.full_name,
            "enabled": self.enabled,
            "provider": self.provider
        }
    
    @property
    def token(self) -> str:
        """
        Generate the JWT token string from the instance data.
        
        Returns:
            str: The encoded JWT token.
        """
        header = {"alg": "HS256", "typ": "JWT"}
        header_base64 = to_base64(header)
        payload_base64 = to_base64(self.payload)
        
        signature = hashlib.sha256(
            f"{header_base64}.{payload_base64}.{JWT_SECRET}".encode("utf-8")
        ).hexdigest()
        return f"{header_base64}.{payload_base64}.{signature}"
    
    @property
    def is_expired(self) -> bool:
        """
        Check if the JWT token is expired.
        
        Returns:
            bool: True if the token is expired, False otherwise.
        """
        current_time = time.time()
        return current_time > self.exp
    
    @staticmethod
    def guest_token() -> 'JsonWebToken':
        """
        Create a JWT token for guest users.
        
        Returns:
            JsonWebToken: An instance of JsonWebToken for guest access.
        """
        return JsonWebToken(
            sub=str(uuid.uuid4()),
            iat=int(time.time()),
            exp=int(time.time()) + config.getint("JWT", "EXPIRATION"),
            role="guest",
            full_name="Guest",
            enabled=True,
            provider=None
        )
    
    @staticmethod
    def from_token(token: str) -> 'JsonWebToken':
        """
        Decode a JWT token string into a JsonWebToken instance, if the signature is valid.
        
        Args:
            token (str): The JWT token to decode.
            
        Returns:
            JsonWebToken: An instance of JsonWebToken with the decoded data.
        """
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token format")
        
        header_base64, payload_base64, signature = parts
        payload = json.loads(base64.b64decode(payload_base64).decode("utf-8"))
        
        expected_signature = hashlib.sha256(
            f"{header_base64}.{payload_base64}.{JWT_SECRET}".encode("utf-8")
        ).hexdigest()
        
        if signature != expected_signature:
            raise ValueError("Invalid token signature")
        
        return JsonWebToken(
            sub=payload["sub"],
            iat=payload["iat"],
            exp=payload["exp"],
            role=payload["role"],
            full_name=payload["full_name"],
            enabled=payload["enabled"],
            provider=payload.get("provider")
        )
    
    @staticmethod
    def from_identity(user_identity: UserIdentity, expire: int = None) -> 'JsonWebToken':
        """
        Create a JsonWebToken instance from a UserIdentityORM object.
        
        Args:
            user_identity (UserIdentityORM): The user identity data object.
            expire (int, optional): The expiration time of the token in seconds. Defaults to None (use the default expiration time from the config).
        
        Returns:
            JsonWebToken: An instance of JsonWebToken with the user's identity data.
        """
        with users_repository.create_session() as user_session:
            user = user_session.get_first({'id': user_identity.user_id})
            if not user:
                raise ValueError("User not found for the given identity")
        
        return JsonWebToken.from_user(user, provider=user_identity.provider, expire=expire)
    
    @staticmethod
    def from_user(user: User, provider: str = None, expire: int = None):
        """
        Create a JsonWebToken instance from a UserORM object.
        
        Args:
            user (UserORM): The user data object.
            provider (str, optional): The identity provider (e.g., 'local', 'cilogon', None for guest).
            expire (int, optional): The expiration time of the token in seconds. Defaults to None (use the default expiration time from the config).
        
        Returns:
            JsonWebToken: An instance of JsonWebToken with the user's data.
        """
        current_time = time.time()
        if expire is None:
            expiration_time = current_time + config.getint("JWT", "EXPIRATION")
        else:
            expiration_time = current_time + expire
        
        return JsonWebToken(
            sub=user.id,
            iat=int(current_time),
            exp=int(expiration_time),
            role=user.role,
            full_name=user.full_name,
            enabled=user.enabled,
            provider=provider
        )
    
    @property
    def identity(self) -> UserIdentity:
        """
        Get the UserIdentity object associated with this token.
        
        Returns:
            UserIdentity: The user identity object.
        """
        with user_identities_repository.create_session() as session:
            return session.get_first({
                'user_id': self.sub,
                'provider': self.provider
            })
            
    @property
    def user(self) -> User:
        """
        Get the User object associated with this token.
        
        Returns:
            User: The user object.
        """
        with users_repository.create_session() as session:
            return session.get_first({
                'id': self.sub
            })

def create_token(user: UserORM, provider: str = None, expire: int = None) -> tuple[str, dict]:
    """
    Create a JSON Web Token (JWT) for the given user data, and return the token and its payload.

    Args:
        user (UserORM): The user data object.
        provider (str, optional): The identity provider (e.g., 'local', 'cilogon', None for guest).
        expire (int, optional): The expiration time of the token in seconds. Defaults to None (use the default expiration time from the config).

    Returns:
        tuple[str, dict]: The generated JWT and its payload.
    """
    jwt = JsonWebToken.from_user(user, provider=provider, expire=expire)
    return jwt.token, jwt.payload

def decode_token(token: str) -> dict:
    """
    Decode a JSON Web Token (JWT) and return its payload.

    Args:
        token (str): The JWT to decode.

    Returns:
        dict: The payload of the JWT.
    """
    try:
        jwt = JsonWebToken.from_token(token)
        return jwt.payload
    except (ValueError, json.JSONDecodeError, KeyError):
        return None


def verify_token(token: str) -> bool:
    """
    Verify the validity of a JSON Web Token (JWT).

    Args:
        token (str): The JWT to verify.

    Returns:
        bool: True if the token is valid, False otherwise.
    """
    try:
        jwt = JsonWebToken.from_token(token)
        return not jwt.is_expired
    except (ValueError, json.JSONDecodeError, KeyError):
        return False


def create_session_token(username: str, password: str) -> str:
    """
    Create a session token for the user with the given username and password.

    Args:
        username (str): The username of the user.
        password (str): The password of the user.

    Returns:
        str: The generated session token.

    Raises:
        Exception: If the credentials are invalid.
    """
    # Look up user identity for local authentication
    with user_identities_repository.create_session() as identity_session:
        user_identity = identity_session.get_first({
            'provider': 'local',
            'provider_user_id': username
        })
        
        if user_identity is None:
            print(f"User {username} not found")
            raise Exception("INVALID_CREDENTIALS")
        
        # Validate password
        hashed_password = hash_password(password)
        if user_identity.password != hashed_password:
            print(f"Invalid password for user {username}")
            raise Exception("INVALID_CREDENTIALS")
        
        user_id = user_identity.user_id
    
    # Get user data
    with users_repository.create_session() as user_session:
        user = user_session.get_first({'id': user_id})
        if user is None:
            print(f"User record not found for ID {user_id}")
            raise Exception("INVALID_CREDENTIALS")
    
    print(f"Password validation successful for {username}")
    token, payload = create_token(user, provider='local')
    return token

def create_token_from_identity(user_identity) -> str:
    """
    Create a JWT token from a user identity record.

    Args:
        user_identity: UserIdentity object from the database.

    Returns:
        str: The generated JWT token.
    """
    jwt = JsonWebToken.from_identity(user_identity)
    return jwt.token


def create_guest_token() -> str:
    """
    Create a JWT token for guest users.

    Returns:
        str: The generated JWT token for guest access.
    """
    jwt = JsonWebToken.guest_token()
    return jwt.token

def disable_sessions_for_user(username: str) -> bool:
    """Deprecated: Session management is now stateless with JWT tokens."""
    return True


def get_most_recent_session_path(username: str) -> dict:
    """Deprecated: Session management is now stateless with JWT tokens."""
    return None

# TODO: CILogon integration
def get_user_data(username: str) -> User | None:
    """
    Retrieve user data by username.
    
    Args:
        username (str): The username of the user.
        
    Returns:
        UserORM | None: The user data object if found, otherwise None.
    """
    with users_repository.create_session() as session:
        return session.get_first({'username': username})

def finalise_token_creation(username: str, user_data: dict) -> str | None:
    """
    Creates new token.
    Returns the new token string or None on failure.
    """

    # Create the new JWT
    token, payload = create_token(user_data)
    if not token or not payload:
        print(f"Failed to create token for user {username}")
        return None
    return token

def create_token_after_external_auth(
    external_user_details: dict,
) -> str | None:
    """
    Finds a user based on external details and generates a token.
    Returns token string or None on failure.
    """
    username = external_user_details.get("username")

    if not username:
        print("External user details missing required email field.")
        return None

    user_data = get_user_data(username)

    if user_data is None:
        print(f"User '{username}' not found.")
        return None
    else:
        return finalise_token_creation(username, user_data)