from itsdangerous import URLSafeTimedSerializer
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

SECRET_KEY = config['APP']['STATE_COOKIE_SECRET']
SALT = config['APP']['SALT']
MAX_AGE_SECONDS = 600 # In seconds (10 minutes)

serializer = URLSafeTimedSerializer(SECRET_KEY, salt=SALT)

def sign_state_data(data):
    """Signs data (like state and next_url) into a secure string."""
    return serializer.dumps(data)

def verify_signed_state_data(signed_data):
    """Verifies the signed string and returns original data if valid and not expired."""
    try:
        data = serializer.loads(signed_data, max_age=MAX_AGE_SECONDS)
        return data
    except Exception:
        return None
