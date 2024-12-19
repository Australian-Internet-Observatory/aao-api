import datetime
import json

import dateutil.tz
from middlewares.authenticate import authenticate
from routes import route
import s3
from utils import Response, use

@route('medias', 'GET')
@use(authenticate)
def get_media(event, response: Response):
    """Get a media file from S3 from a given path in the query string.
    
    The path should be a key in the S3 bucket.
    ---
    tags:
        - media
    parameters:
        - in: query
          name: path
          required: true
          schema:
              type: string
          description: The path to the media file in the S3 bucket
    responses:
        200:
            description: A successful response
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            path:
                                type: string
                            url:
                                type: string
        404:
            description: File not found
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                                example: False
                            comment:
                                type: string
                                example: 'FILE_NOT_FOUND'
    """
    path = event['queryStringParameters']['path']
    client = s3.client
    
    try:
        # Get a presigned URL for the media file
        url = client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': s3.MOBILE_OBSERVATIONS_BUCKET,
                'Key': path
            },
        )
        
        # Return the URL
        return response.json({
            'success': True,
            'path': path,
            'presigned_url': url
        })
    except Exception as e:
        return response.status(404).json({
            'success': False,
            'comment': 'FILE_NOT_FOUND'
        })