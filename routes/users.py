from routes import route
from middlewares.authenticate import authenticate
from utils import use, jwt
import hashlib
import boto3
import json

from configparser import ConfigParser
config = ConfigParser()
config.read('config.ini')

session = boto3.Session(
    aws_access_key_id=config['AWS']['ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS']['SECRET_ACCESS_KEY'],
    region_name='ap-southeast-2'
)

@route('users')
@use(authenticate)
def list_users():
    """Returns a list of users from the S3 bucket

    Returns a list of users stored in the S3 bucket.
    ---
    tags:
        - users

    responses:
        200:
            description: A successful response
            content:
                application/json:
                    schema:
                        type: array
                        items:
                            type: object
        400:
            description: A failed response
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                            comment:
                                type: string
    """
    s3 = session.client('s3')
    user_objects = s3.list_objects_v2(
        Bucket='fta-mobile-observations-holding-bucket',
        Prefix='metadata/dashboard-users/'
    )
    keys = [user['Key'] for user in user_objects['Contents'] if user['Key'].endswith('credentials.json')]
    users = []
    for key in keys:
        user_object = s3.get_object(
            Bucket='fta-mobile-observations-holding-bucket',
            Key=key
        )
        user_data = json.loads(user_object['Body'].read().decode('utf-8'))
        users.append(user_data)
    return users

@route('users/edit')
@use(authenticate)
def edit_user(event):
    """Edit a user in the S3 bucket

    Edit a user's information stored in the S3 bucket.
    ---
    tags:
        - users
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        username:
                            type: string
                        enabled:
                            type: boolean
                        password:
                            type: string
                        full_name:
                            type: string
                        role:
                            type: string
    responses:
        200:
            description: A successful edit
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                            comment:
                                type: string
        400:
            description: A failed edit
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                            comment:
                                type: string
    """
    s3 = session.client('s3')
    username = event['data']['username']
    user_object = None
    try:
        user_object = s3.get_object(
            Bucket='fta-mobile-observations-holding-bucket',
            Key=f'metadata/dashboard-users/{username}/credentials.json'
        )
    except Exception as e:
        return {
            "success": False,
            "comment": "User not found"
        }
    old_data = json.loads(user_object['Body'].read().decode('utf-8'))
    new_data = event['data']
    
    acceptable_fields = ['enabled', 'password', 'full_name', 'role']
    
    # Ensure that the fields are acceptable
    for key in new_data:
        if key not in acceptable_fields:
            return {
                "success": False,
                "comment": "INVALID_FIELD: " + key
            }
    
    # Update the user data
    combined_data = {**old_data, **new_data}
    s3.put_object(
        Bucket='fta-mobile-observations-holding-bucket',
        Key=f'metadata/dashboard-users/{username}/credentials.json',
        Body=json.dumps(combined_data).encode('utf-8')
    )
    return {
        "success": True,
        "comment": "User updated successfully"
    }

if __name__ == "__main__":
    print(list_users())