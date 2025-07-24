from dataclasses import dataclass
import os

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
    test: TestConfig
    
def _load_from_file(target = 'config.ini') -> Config:
    import configparser
    _config = configparser.ConfigParser()
    _config.read(target)
    
    return Config(
        aws=AwsConfig(
            access_key_id=_config['AWS']['ACCESS_KEY_ID'],
            secret_access_key=_config['AWS']['SECRET_ACCESS_KEY'],
            region=_config['AWS']['REGION']
        ),
        deployment=DeploymentConfig(
            lambda_function_name=_config['DEPLOYMENT']['LAMBDA_FUNCTION_NAME'],
            zip_file=_config['DEPLOYMENT']['ZIP_FILE'],
            deployment_bucket=_config['DEPLOYMENT']['DEPLOYMENT_BUCKET']
        ),
        jwt=JwtConfig(
            secret=_config['JWT']['SECRET'],
            expiration=int(_config['JWT']['EXPIRATION'])
        ),
        open_search=OpenSearchConfig(
            endpoint=_config['OPEN_SEARCH']['ENDPOINT']
        ),
        postgres=PostgresConfig(
            host=_config['POSTGRES']['HOST'],
            port=int(_config['POSTGRES']['PORT']),
            database=_config['POSTGRES']['DATABASE'],
            username=_config['POSTGRES']['USERNAME'],
            password=_config['POSTGRES']['PASSWORD']
        ),
        cilogon=CilogonConfig(
            client_id=_config['CILOGON']['CLIENT_ID'],
            client_secret=_config['CILOGON']['CLIENT_SECRET'],
            metadata_url=_config['CILOGON']['METADATA_URL'],
            redirect_uri=_config['CILOGON']['REDIRECT_URI']
        ),
        app=AppConfig(
            state_cookie_secret=_config['APP']['STATE_COOKIE_SECRET'],
            salt=_config['APP']['SALT'],
            frontend_url=_config['APP']['FRONTEND_URL']
        ),
        test=TestConfig(
            username=_config['TEST']['USERNAME'],
            password=_config['TEST']['PASSWORD']
        )
    )

import os

print("Loading configuration for environment:", os.getenv('ENV', 'unknown'))

if os.getenv('ENV') == 'documentation':
    config = _load_from_file('sample_config.ini')
else:
    config = _load_from_file('config.ini')