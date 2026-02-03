"""
API Key utilities for generation, hashing, and verification.

This module provides functions for securely managing API keys, including:
- Generating random API keys
- Hashing API keys for storage
- Verifying API keys against stored hashes
- Retrieving users associated with API keys
- Updating last_used_at timestamps
"""

import secrets
import time
import bcrypt
from typing import Tuple, Optional
from config import config
from models.api_key import ApiKey
from models.user import User
from db.shared_repositories import api_keys_repository, users_repository


def generate_api_key() -> Tuple[str, str, str]:
    """
    Generate a new API key.
    
    Returns:
        Tuple containing:
        - full_key: The complete API key to show to the user (64 URL-safe characters)
        - hashed_key: The bcrypt hash of the key for storage
        - suffix: The last 6 characters for display purposes
    """
    # Generate a 64-byte random key (results in ~86 URL-safe characters)
    full_key = secrets.token_urlsafe(64)
    
    # Hash the key with bcrypt
    hashed_key = hash_api_key(full_key)
    
    # Extract last 6 characters as suffix
    suffix = full_key[-6:]
    
    return full_key, hashed_key, suffix


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using bcrypt with the configured salt.
    
    Args:
        api_key: The plain text API key to hash
        
    Returns:
        The bcrypt hash of the API key as a string
    """
    # Combine API key with server salt
    salted_key = f"{api_key}{config.api_key.salt}"
    
    # Hash using bcrypt
    hashed = bcrypt.hashpw(salted_key.encode('utf-8'), bcrypt.gensalt())
    
    return hashed.decode('utf-8')


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """
    Verify an API key against its stored hash.
    
    Args:
        api_key: The plain text API key to verify
        hashed_key: The stored bcrypt hash
        
    Returns:
        True if the key matches the hash, False otherwise
    """
    try:
        # Combine API key with server salt
        salted_key = f"{api_key}{config.api_key.salt}"
        
        # Verify using bcrypt
        return bcrypt.checkpw(salted_key.encode('utf-8'), hashed_key.encode('utf-8'))
    except Exception:
        return False


def get_api_key_entity(api_key: str) -> Optional[User]:
    """
    Retrieve the user associated with a given API key.
    
    This function:
    1. Retrieves all API keys from the database
    2. Verifies the provided key against each hashed key
    3. Returns the associated user if found
    
    Args:
        api_key: The plain text API key
        
    Returns:
        User object if the key is valid, None otherwise
    """
    with api_keys_repository.create_session() as session:
        key_suffix = api_key[-6:]
        api_key_record = session.get_first({'suffix': key_suffix})
        print(f"[API Key] Valid API key used: {api_key_record}")
        if api_key_record and verify_api_key(api_key, api_key_record.hashed_key):
            with users_repository.create_session() as user_session:
                user = user_session.get_first({'id': api_key_record.user_id})
                return api_key_record, user
    
    return None, None


def update_last_used(api_key_id: str) -> None:
    """
    Update the last_used_at timestamp for an API key.
    
    Args:
        api_key_id: The ID of the API key to update
    """
    with api_keys_repository.create_session() as session:
        api_key = session.get_first({'id': api_key_id})
        if api_key:
            api_key.last_used_at = int(time.time())
            session.update(api_key)


def is_api_key_exists(api_key_id: str) -> bool:
    """
    Check if an API key exists by ID.
    
    Args:
        api_key_id: The ID of the API key
        
    Returns:
        True if the key exists, False otherwise
    """
    with api_keys_repository.create_session() as session:
        api_key = session.get_first({'id': api_key_id})
        return api_key is not None


def get_api_key_by_id(api_key_id: str) -> Optional[ApiKey]:
    """
    Retrieve an API key by its ID.
    
    Args:
        api_key_id: The ID of the API key
        
    Returns:
        ApiKey object if found, None otherwise
    """
    with api_keys_repository.create_session() as session:
        return session.get_first({'id': api_key_id})


def get_user_api_keys(user_id: str) -> list[ApiKey]:
    """
    Retrieve all API keys for a specific user.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        List of ApiKey objects
    """
    with api_keys_repository.create_session() as session:
        keys = session.get({'user_id': user_id})
        return keys if keys else []


def delete_api_key(api_key_id: str) -> bool:
    """
    Delete an API key by its ID.
    
    Args:
        api_key_id: The ID of the API key to delete
        
    Returns:
        True if deleted successfully, False if not found
    """
    with api_keys_repository.create_session() as session:
        api_key = session.get_first({'id': api_key_id})
        if api_key:
            session.delete(api_key)
            return True
        return False
