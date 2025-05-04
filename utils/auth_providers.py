import requests
from authlib.integrations.requests_client import OAuth2Session
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

CLIENT_ID = config['CILOGON']['CLIENT_ID']
CLIENT_SECRET = config['CILOGON']['CLIENT_SECRET']
METADATA_URL = config['CILOGON']['METADATA_URL']
REDIRECT_URI = config['CILOGON']['REDIRECT_URI']

def fetch_oidc_metadata(url):
    """Fetches the OIDC metadata as creating a client does not fetch it automatically"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching OIDC metadata: {e}")
        return {}

metadata = fetch_oidc_metadata(METADATA_URL)

client = OAuth2Session(
    CLIENT_ID,
    CLIENT_SECRET,
    scope="openid email profile org.cilogon.userinfo",
    redirect_uri=REDIRECT_URI
)

client.metadata = metadata