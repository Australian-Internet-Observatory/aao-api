from dataclasses import dataclass
import configparser
import os
from dotenv import load_dotenv

@dataclass
class AwsConfig:
    access_key_id: str
    secret_access_key: str
    region: str
    
@dataclass
class DeploymentConfig:
    lambda_function_name: str
    zip_file: str
    deployment_bucket: str
    
@dataclass
class JwtConfig:
    secret: str
    expiration: int
    
@dataclass
class OpenSearchConfig:
    endpoint: str
    
@dataclass
class PostgresConfig:
    host: str
    port: int
    database: str
    username: str
    password: str
    
@dataclass
class CilogonConfig:
    client_id: str
    client_secret: str
    metadata_url: str
    redirect_uri: str
    
@dataclass
class AppConfig:
    state_cookie_secret: str
    salt: str
    frontend_url: str

@dataclass
class ExternalApiConfig:
    ad_delete_lambda_key: str
    
@dataclass
class BucketsConfig:
    observations: str
    metadata: str
    
@dataclass
class TestConfig:
    username: str
    password: str
    
@dataclass
class Config:
    aws: AwsConfig
    deployment: DeploymentConfig
    jwt: JwtConfig
    open_search: OpenSearchConfig
    postgres: PostgresConfig
    cilogon: CilogonConfig
    app: AppConfig
    external_api: ExternalApiConfig
    buckets: BucketsConfig
    test: TestConfig

def _create_config(config) -> Config:
    return Config(
        aws=AwsConfig(
            access_key_id=config['AWS']['ACCESS_KEY_ID'],
            secret_access_key=config['AWS']['SECRET_ACCESS_KEY'],
            region=config['AWS']['REGION']
        ),
        deployment=DeploymentConfig(
            lambda_function_name=config['DEPLOYMENT']['LAMBDA_FUNCTION_NAME'],
            zip_file=config['DEPLOYMENT']['ZIP_FILE'],
            deployment_bucket=config['DEPLOYMENT']['DEPLOYMENT_BUCKET']
        ),
        jwt=JwtConfig(
            secret=config['JWT']['SECRET'],
            expiration=int(config['JWT']['EXPIRATION'])
        ),
        open_search=OpenSearchConfig(
            endpoint=config['OPEN_SEARCH']['ENDPOINT']
        ),
        postgres=PostgresConfig(
            host=config['POSTGRES']['HOST'],
            port=int(config['POSTGRES']['PORT']),
            database=config['POSTGRES']['DATABASE'],
            username=config['POSTGRES']['USERNAME'],
            password=config['POSTGRES']['PASSWORD']
        ),
        cilogon=CilogonConfig(
            client_id=config['CILOGON']['CLIENT_ID'],
            client_secret=config['CILOGON']['CLIENT_SECRET'],
            metadata_url=config['CILOGON']['METADATA_URL'],
            redirect_uri=config['CILOGON']['REDIRECT_URI']
        ),
        app=AppConfig(
            state_cookie_secret=config['APP']['STATE_COOKIE_SECRET'],
            salt=config['APP']['SALT'],
            frontend_url=config['APP']['FRONTEND_URL']
        ),
        external_api=ExternalApiConfig(
            ad_delete_lambda_key=config['EXTERNAL_API']['AD_DELETE_LAMBDA_KEY']
        ),
        buckets=BucketsConfig(
            observations=config['BUCKETS']['OBSERVATIONS'],
            metadata=config['BUCKETS']['METADATA']
        ),
        test=TestConfig(
            username=config['TEST']['USERNAME'],
            password=config['TEST']['PASSWORD']
        )
    )

def _load_from_file(target = 'config.ini') -> Config:
    _config = configparser.ConfigParser()
    _config.read(target)
    
    return _create_config(_config)

def from_string(str: str) -> Config:
    _config = configparser.ConfigParser()
    _config.read_string(str)
    
    return _create_config(_config)

import os

load_dotenv(verbose=True)
print("Loading configuration for environment:", os.getenv('ENV', 'unknown'))

if os.getenv('ENV') == 'documentation':
    config = _load_from_file('sample_config.ini')
else:
    config = _load_from_file('config.ini')