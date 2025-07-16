import json
import boto3
import os
import sys
from datetime import datetime

from configparser import ConfigParser
config = ConfigParser()
config.read('config.ini')

class ConsoleColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    DEFAULT = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

session = boto3.Session(
    aws_access_key_id=config['AWS']['ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS']['SECRET_ACCESS_KEY']
)

lambda_client = session.client('lambda', region_name=config['AWS']['REGION'])
s3_client = session.client('s3', region_name=config['AWS']['REGION'])

zip_file = config['DEPLOYMENT']['ZIP_FILE']
function_name = config['DEPLOYMENT']['LAMBDA_FUNCTION_NAME']
deployment_bucket = config['DEPLOYMENT']['DEPLOYMENT_BUCKET']

def is_possibly_dev_environment():
    """Check if the current environment is possibly a development environment.
    
    This can be used to guard against accidental deployments to production.
    """
    KEYWORDS = ['dev', 'development', 'test', 'staging']
    POSSIBLE_CONFIG_FIELDS = [
        ('DEPLOYMENT', 'LAMBDA_FUNCTION_NAME'),
        ('DEPLOYMENT', 'ZIP_FILE'),
        ('POSTGRES', 'DATABASE'),
    ]
    for section, key in POSSIBLE_CONFIG_FIELDS:
        value = config.get(section, key, fallback='').lower()
        if any(keyword in value for keyword in KEYWORDS):
            print(f'Warning: {section}.{key} contains a development keyword: {value}')
            return True
    return False

# Get stage (deployment folder) from command line argument or use default
# TODO: Consider making "dev" the default deployment folder
if len(sys.argv) < 2:
    stage = "prod"
    print(f"No stage specified, using default: {stage}")
else:
    stage = sys.argv[1]

def upload_to_s3(file_path, bucket, key):
    """Upload a file to S3 and return the S3 URL."""
    try:
        print(f'Uploading {file_path} to s3://{bucket}/{key}')
        s3_client.upload_file(file_path, bucket, key)
        print(f'Successfully uploaded to S3')
        return f's3://{bucket}/{key}'
    except Exception as e:
        print(f'Error uploading to S3: {str(e)}')
        raise

def deploy_lambda():
    """Deploy the Lambda function using the specified zip file.
    
    This function uploads the zip file to S3 and updates the Lambda function to use the code from the S3 bucket.
    """
    if stage.lower() == 'prod' and is_possibly_dev_environment():
        print(f"{ConsoleColors.WARNING}[WARNING] You are deploying to production with a configuration that may indicate a development environment.{ConsoleColors.DEFAULT}")
        confirmation = input("Do you want to continue? (yes/no): ").strip().lower()
        if confirmation != 'yes':
            print("Deployment cancelled.")
            return
    
    # Check if zip file exists
    if not os.path.exists(zip_file):
        print(f'Error: {zip_file} does not exist')
        return
    
    # Get file size
    file_size = os.path.getsize(zip_file)
    print(f'Zip file size: {file_size / (1024 * 1024):.2f} MB')
    print(f'Deployment folder: {stage}')
    
    # Generate S3 key with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    s3_key = f'{stage}/{function_name}_{timestamp}.zip'
    
    try:
        # Upload to S3
        s3_url = upload_to_s3(zip_file, deployment_bucket, s3_key)
        
        # Update Lambda function using S3 URL
        print(f'Updating {function_name} with S3 package: {s3_url}')
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            S3Bucket=deployment_bucket,
            S3Key=s3_key,
            Publish=True
        )
        
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print(f'{function_name} updated successfully')
            print(f'Function ARN: {response.get("FunctionArn", "N/A")}')
            print(f'Version: {response.get("Version", "N/A")}')
        else:
            print(f'Error updating {function_name}')
            print(json.dumps(response, indent=2))
            
    except Exception as e:
        print(f'Deployment failed: {str(e)}')
    
deploy_lambda()