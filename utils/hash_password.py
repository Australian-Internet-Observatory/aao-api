import hashlib

def hash_password(password: str) -> str:
    """
    Hashes a password using MD5.

    :param password: The password to hash.
    :return: The hashed password as a hexadecimal string.
    """
    return hashlib.md5(password.encode('utf-8')).hexdigest()