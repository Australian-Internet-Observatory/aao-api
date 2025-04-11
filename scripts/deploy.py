import json
import boto3

from configparser import ConfigParser
config = ConfigParser()
config.read('config.ini')

session = boto3.Session(
    aws_access_key_id=config['AWS']['ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS']['SECRET_ACCESS_KEY']
)

lambda_client = session.client('lambda', region_name=config['AWS']['REGION'])

zip_file = config['DEPLOYMENT']['ZIP_FILE']
function_name = config['DEPLOYMENT']['LAMBDA_FUNCTION_NAME']

def deploy_lambda():
    with open(zip_file, 'rb') as f:
        zipped_code = f.read()
        size = len(zipped_code)
        print(f'Zip file size: {size / (1024 * 1024):.2f} MB')
    print(f'Updating {function_name} with {zip_file}')
    response = lambda_client.update_function_code(
        FunctionName=function_name,
        ZipFile=zipped_code,
        Publish=True
    )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print(f'{function_name} updated successfully')
    else:
        print(f'Error updating {function_name}')
        print(json.dumps(response, indent=2))
    # print(json.dumps(response, indent=2))
    
deploy_lambda()