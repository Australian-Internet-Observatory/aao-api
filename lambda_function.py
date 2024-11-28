import datetime
import dateutil.tz
from middlewares import parse_body
from middlewares.authenticate import authenticate
from routes import route
from utils import use
import base64
import json
from routes import routes
import s3

@route('list-observers', 'GET')
@use(authenticate)
# Event not used directly, but needed to authenticate
def list_observers(event):
    """List all observers.

    Retrieve a list of all observers from the S3 bucket.
    ---
    tags:
        - observers

    responses:
        200:
            description: A successful response
            content:
                application/json:
                    schema:
                        type: array
                        items:
                            type: string
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
    dirs = s3.list_dir()
    return [path for path in dirs if path.endswith("/")]

@route('get-access-cache', 'POST') # get-access-cache?observer_id=5ea80108-154d-4a7f-8189-096c0641cd87
@use(authenticate)
def get_access_cache(event, response):
    """Retrieve the access cache for an observer.

    Retrieve the quick access cache for the specified observer.
    ---
    tags:
        - observers
    parameters:
        - in: query
          name: observer_id
          required: true
          schema:
              type: string
    responses:
        200:
            description: A successful response
            content:
                application/json:
                    schema:
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
    observer_id = event['queryStringParameters'].get('observer_id', None)
    if observer_id is None:
        return response.status(400).json({
            'success': False,
            'comment': 'OBSERVER_NOT_PROVIDED'
        })
    if observer_id.endswith('/'):
        observer_id = observer_id[:-1]
    observer_data = s3.read_json_file(f'{observer_id}/quick_access_cache.json')
    if observer_data is None:
        return response.status(404).json({
            'success': False,
            'comment': 'NO_CACHE_FOUND'
        })
    
    return {
        'success': True,
        'data': observer_data
    }
    
@route('get-frames-presigned', 'POST') # get-frames?path=5ea80108-154d-4a7f-8189-096c0641cd87/temp/1729261457039.c979d19c-0546-412b-a2d9-63a247d7c250
@use(authenticate)
def get_frames_presigned(event, response):
    """Get the presigned URLs for the frames of an ad.

    Retrieve presigned URLs for the frames of the specified ad.
    ---
    tags:
        - ads
    parameters:
        - in: query
          name: path
          required: true
          schema:
              type: string
    responses:
        200:
            description: A successful response
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                            frame_paths:
                                type: array
                                items:
                                    type: string
                            presigned_urls:
                                type: array
                                items:
                                    type: string
        400:
            description: A failed response
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                                example: false
                            comment:
                                type: string
                                example: 'PATH_NOT_PROVIDED'
    """
    path = event['queryStringParameters'].get('path', None)
    if path is None:
        return response.status(400).json({
            'success': False,
            'comment': 'PATH_NOT_PROVIDED'
        })
    
    if not path.endswith('/'):
        path += '/'
    # List the frames at the path
    frames = s3.list_dir(path)
    frame_paths = [f'{frame}' for frame in frames]
    
    # Generate presigned URLs for each frame
    presigned_urls = []
    image_extensions = ['.jpg', '.jpeg', '.png']
    for frame_path in frame_paths:
        if not any([frame_path.endswith(ext) for ext in image_extensions]):
            continue
        presigned_url = s3.client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': s3.MOBILE_OBSERVATIONS_BUCKET,
                'Key': frame_path
            }
        )
        presigned_urls.append(presigned_url)
    
    return {
        'success': True,
        'frame_paths': frame_paths,
        'presigned_urls': presigned_urls
    }
    
def try_compute_ads_stream_index():
    """Compute the ads stream index from the quick_access_cache.json file across
    all observers and save it to the ads_stream.json file in the root of the bucket.
    
    Does not run if the ads_stream.json file already exists and not older than 24 hours.
    """
    # Check if the ads_stream.json file exists and is not older than 24 hours
    INDEX_FILENAME = 'ads_stream.json'
    index_obj = s3.try_get_object(key=INDEX_FILENAME)
    if index_obj is not None:
        # Terminate if the file is not older than 24 hours
        last_modified = index_obj['LastModified']
        now = datetime.datetime.now(tz=dateutil.tz.tzutc())
        cache_age = now - last_modified
        print(f'Found cache file. Cache age: {cache_age}')
        if cache_age < datetime.timedelta(days=1):
            return s3.read_json_file(INDEX_FILENAME)

    # List all observers
    print('Cache expired or not found. Computing ads stream index...')
    observers = s3.list_dir()
    
    ads_stream_index = {}
    # For each observer, 
    #   read the quick_access_cache.json file and
    #   compute the ads stream index
    for observer_id in observers:
        if observer_id.endswith('/'):
            observer_id = observer_id[:-1]
        observer_data = s3.read_json_file(f'{observer_id}/quick_access_cache.json')
        if observer_data is None:
            continue
        keys = observer_data.keys()
        for key in keys:
            # Exclude 'observations' - too much unnecessary data
            if key == 'observations':
                continue
            if key not in ads_stream_index:
                ads_stream_index[key] = []
            ads_stream_index[key].extend(observer_data[key])
    
    keys = ads_stream_index.keys()
    
    # value structure: fda7681c-d7f1-4420-8499-46b4695d224a/temp/1729261457039.c979d19c-0546-412b-a2d9-63a247d7c250/
    # observer: fda7681c-d7f1-4420-8499-46b4695d224a
    # timestamp: 1729261457039
    # ad_id: c979d19c-0546-412b-a2d9-63a247d7c250
    # Sort the ads stream index by timestamp
    def sort_by_timestamp(value):
        if value.endswith('/'):
            value = value[:-1]
        observer, _, ad_path = value.split('/')
        try:
            timestamp, ad_id = ad_path.split('.')
            return int(timestamp)
        except Exception as e:
            return 0
    
    for key in keys:
        ads_stream_index[key] = sorted(ads_stream_index[key], key=sort_by_timestamp)
    
    print("Writing ads stream index to files...")
    # Save the ads stream index to the ads_stream.json file
    s3.client.put_object(
        Bucket=s3.MOBILE_OBSERVATIONS_BUCKET,
        Key=INDEX_FILENAME,
        Body=json.dumps(ads_stream_index).encode('utf-8')
    )
    return ads_stream_index

@route('list-ads', 'GET')
@use(authenticate)
def get_ads_stream_index(event, response):
    """Retrieve the ads stream index.

    Retrieve the ads stream index from the S3 bucket, or recompute it if it is older than 24 hours.
    ---
    tags:
        - ads

    responses:
        200:
            description: A successful response
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                            presigned_url:
                                type: string
        500:
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
                            error:
                                type: string
    """
    try:
        try_compute_ads_stream_index()
        INDEX_FILENAME = 'ads_stream.json'
        presigned_url = s3.client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': s3.MOBILE_OBSERVATIONS_BUCKET,
                'Key': INDEX_FILENAME
            }
        )
        return {
            'success': True,
            'presigned_url': presigned_url
        }
    except Exception as e:
        return response.status(500).json({
            'success': False,
            'comment': f'FAILED_TO_COMPUTE_ADS_STREAM_INDEX',
            'error': str(e)
        })

@route('reflect', 'POST')
def reflect(event):
    """Reflect the event back to the client.
    
    Return the event object as the response.
    ---
    requestBody:
        required: false
        content:
            application/json:
                schema:
                    type: object
    responses:
        200:
            description: A successful reflection
            content:
                application/json:
                    schema:
                        type: object
        400:
            description: A failed reflection
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
    return event

@route('/hello', 'GET')
def hello():
    return {'message': 'Hello, world!'}

def lambda_handler(event_raw, context):
    try:
        event, response, context = parse_body(event_raw, context, None)
        
        route = event['path']
        method = event['httpMethod']
        if not route.startswith('/'):
            route = f'/{route}'
        
        if route in routes and method in routes[route]:
            action = routes[route][method]
            _, response, _ = action(event, response, context)
            return response.body

        return {
            'statusCode': 404,
            'isBase64Encoded': False,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({
                'success': False,
                'comment': 'ACTION_NOT_FOUND',
                'error': f'No route found for "{route}" with method "{method}"'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'isBase64Encoded': False,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({
                'success': False,
                'comment': 'INTERNAL_SERVER_ERROR',
                'error': str(e)
            })
        }
    
if __name__ == "__main__":
    # data = {
    #     'action': 'list-observers',
    #     'data': {
    #         'session_token': 'e49c1d01-8ff3-4192-bce0-a1d15812e98c'
    #     }
    # }
    # data = {
    #     'action': 'get-access-cache',
    #     'data': {
    #         'session_token': 'e49c1d01-8ff3-4192-bce0-a1d15812e98c',
    #         'observer': '5ea80108-154d-4a7f-8189-096c0641cd87'
    #     }
    # }
    # event = {
    #     'path': 'users',
    #     'httpMethod': 'GET',
    #     'headers': {
    #         'Authorization': "Bearer eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VybmFtZSI6ICJkYW50cmFuIiwgImZ1bGxfbmFtZSI6ICJEYW4gVHJhbiIsICJleHAiOiAxNzMyODU0MDEwLjIyMTk1NjN9.138f6b953c576512724f34af5c8fce443a2a5afc43570b6bedab355d81180677"
    #     }
    # }
    print(routes)
    
    event = {
        'path': 'hello',
        'httpMethod': 'GET'
    }
    context = {}
    print(json.dumps(lambda_handler(event, context), indent=2))