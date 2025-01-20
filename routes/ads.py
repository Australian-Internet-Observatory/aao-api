import datetime
import json

import dateutil.tz
from enricher import RdoBuilder
from middlewares.authenticate import authenticate
from routes import route
import utils.observations_repository as observations_repository
from utils import use
from utils.query import AdQuery

@route('ads/{observer_id}', 'GET') # get-access-cache?observer_id=5ea80108-154d-4a7f-8189-096c0641cd87
@use(authenticate)
def get_access_cache(event, response):
    """Retrieve the access cache for an observer.

    Retrieve the quick access cache for the specified observer.
    ---
    tags:
        - ads
    parameters:
        - in: path
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
                        properties:
                            success:
                                type: boolean
                            data:
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
                                example: False
                            comment:
                                type: string
                                example: 'OBSERVER_NOT_PROVIDED_IN_PATH'
        404:
            description: No cache found for observer
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
                                example: 'NO_CACHE_FOUND_FOR_OBSERVER'
    """
    observer_id = event['pathParameters'].get('observer_id', None)
    if observer_id is None:
        return response.status(400).json({
            'success': False,
            'comment': 'OBSERVER_NOT_PROVIDED_IN_PATH'
        })
    if observer_id.endswith('/'):
        observer_id = observer_id[:-1]
    observer_data = observations_repository.read_json_file(f'{observer_id}/quick_access_cache.json')
    if observer_data is None:
        return response.status(404).json({
            'success': False,
            'comment': 'NO_CACHE_FOUND_FOR_OBSERVER'
        })
    
    return {
        'success': True,
        'data': observer_data
    }

@route('ads/{observer_id}/{timestamp}.{ad_id}/stitching/frames', 'GET') # get-stiching-frames?path=5ea80108-154d-4a7f-8189-096c0641cd87/temp/1729261457039.c979d19c-0546-412b-a2d9-63a247d7c250
@use(authenticate)
def get_stitching_frames_presigned(event, response):
    """Get the presigned URLs for the frames of an ad's stitching.
    
    Retrieve presigned URLs for the frames of the specified ad's stitching, which is the cropped version of the ad that removes the irrelevant parts.
    ---
    tags:
        - ads
    parameters:
        - in: path
          name: observer_id
          required: true
          schema:
              type: string
        - in: path
          name: timestamp
          required: true
          schema:
              type: string
        - in: path
          name: ad_id
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
                                example: False
                            comment:
                                type: string
                                example: 'PATH_NOT_PROVIDED'
    """
    observer_id = event['pathParameters'].get('observer_id', None)
    timestamp = event['pathParameters'].get('timestamp', None)
    ad_id = event['pathParameters'].get('ad_id', None)
    path = f'{observer_id}/stitching/{timestamp}.{ad_id}'
    
    if path is None:
        return response.status(400).json({
            'success': False,
            'comment': 'PATH_NOT_PROVIDED'
        })
    
    if not path.endswith('/'):
        path += '/'
    # List the frames at the path
    frames = observations_repository.list_dir(path)
    # print(s3.list_dir(f'{observer_id}/temp'))
    frame_paths = [f'{frame}' for frame in frames]
    
    # Generate presigned URLs for each frame
    presigned_urls = []
    image_extensions = ['.jpg', '.jpeg', '.png']
    for frame_path in frame_paths:
        if not any([frame_path.endswith(ext) for ext in image_extensions]):
            continue
        presigned_url = observations_repository.client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': observations_repository.MOBILE_OBSERVATIONS_BUCKET,
                'Key': frame_path
            }
        )
        presigned_urls.append(presigned_url)
    
    return {
        'success': True,
        'frame_paths': frame_paths,
        'presigned_urls': presigned_urls
    }

@route('ads/{observer_id}/{timestamp}.{ad_id}/frames', 'GET') # get-frames?path=5ea80108-154d-4a7f-8189-096c0641cd87/temp/1729261457039.c979d19c-0546-412b-a2d9-63a247d7c250
@use(authenticate)
def get_frames_presigned(event, response):
    """Get the presigned URLs for the frames of an ad.

    Retrieve presigned URLs for the frames of the specified ad.
    ---
    tags:
        - ads
    parameters:
        - in: path
          name: observer_id
          required: true
          schema:
              type: string
        - in: path
          name: timestamp
          required: true
          schema:
              type: string
        - in: path
          name: ad_id
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
                                example: False
                            comment:
                                type: string
                                example: 'PATH_NOT_PROVIDED'
    """
    # path = event['queryStringParameters'].get('path', None)
    # Compute the path from the path parameters: {observer_id}/temp/{timestamp}.{ad_id}
    print(event['pathParameters'])
    observer_id = event['pathParameters'].get('observer_id', None)
    timestamp = event['pathParameters'].get('timestamp', None)
    ad_id = event['pathParameters'].get('ad_id', None)
    path = f'{observer_id}/temp/{timestamp}.{ad_id}'
    
    if path is None:
        return response.status(400).json({
            'success': False,
            'comment': 'PATH_NOT_PROVIDED'
        })
    
    if not path.endswith('/'):
        path += '/'
    # List the frames at the path
    frames = observations_repository.list_dir(path)
    print(path)
    # print(s3.list_dir(f'{observer_id}/temp'))
    frame_paths = [f'{frame}' for frame in frames]
    
    # Generate presigned URLs for each frame
    presigned_urls = []
    image_extensions = ['.jpg', '.jpeg', '.png']
    for frame_path in frame_paths:
        if not any([frame_path.endswith(ext) for ext in image_extensions]):
            continue
        presigned_url = observations_repository.client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': observations_repository.MOBILE_OBSERVATIONS_BUCKET,
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
    index_obj = observations_repository.try_get_object(key=INDEX_FILENAME)
    if index_obj is not None:
        # Terminate if the file is not older than 24 hours
        last_modified = index_obj['LastModified']
        now = datetime.datetime.now(tz=dateutil.tz.tzutc())
        cache_age = now - last_modified
        print(f'Found cache file. Cache age: {cache_age}')
        if cache_age < datetime.timedelta(days=1):
            return observations_repository.read_json_file(INDEX_FILENAME)

    # List all observers
    print('Cache expired or not found. Computing ads stream index...')
    observers = observations_repository.list_dir()
    
    ads_stream_index = {}
    # For each observer, 
    #   read the quick_access_cache.json file and
    #   compute the ads stream index
    for observer_id in observers:
        if observer_id.endswith('/'):
            observer_id = observer_id[:-1]
        observer_data = observations_repository.read_json_file(f'{observer_id}/quick_access_cache.json')
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
    observations_repository.client.put_object(
        Bucket=observations_repository.MOBILE_OBSERVATIONS_BUCKET,
        Key=INDEX_FILENAME,
        Body=json.dumps(ads_stream_index).encode('utf-8')
    )
    return ads_stream_index

@route('ads', 'GET')
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
                                example: False
                            comment:
                                type: string
                                example: 'FAILED_TO_COMPUTE_ADS_STREAM_INDEX'
                            error:
                                type: string
    """
    try:
        try_compute_ads_stream_index()
        INDEX_FILENAME = 'ads_stream.json'
        presigned_url = observations_repository.client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': observations_repository.MOBILE_OBSERVATIONS_BUCKET,
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
        
# Rich Data Object composer

def parse_ad_params(event, response, context):
    observer_id = event['pathParameters'].get('observer_id', None)
    timestamp = event['pathParameters'].get('timestamp', None)
    ad_id = event['pathParameters'].get('ad_id', None)
    if observer_id is None or timestamp is None or ad_id is None:
        missing_params = []
        if observer_id is None:
            missing_params.append('observer_id')
        if timestamp is None:
            missing_params.append('timestamp')
        if ad_id is None:
            missing_params.append('ad_id')
        response.status(400).json({
            'success': False,
            'comment': f'MISSING_PARAMETERS: {", ".join(missing_params)}'
        })
        return event, response, context
    event['ad_params'] = [observer_id, timestamp, ad_id]
    return event, response, context

@route('ads/{observer_id}/{timestamp}.{ad_id}/rdo/ocr_data', 'GET')
@use(authenticate)
@use(parse_ad_params)
def get_ad_ocr_data(event, response):
    """Retrieve OCR data for an ad.

    Retrieve OCR data for the specified ad, including text matches and their positions.
    ---
    tags:
        - ads
        - rdo
    parameters:
        - in: path
          name: observer_id
          required: true
          schema:
              type: string
        - in: path
          name: timestamp
          required: true
          schema:
              type: string
        - in: path
          name: ad_id
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
                            ocr_data:
                                type: array
                                items:
                                    type: object
                                    properties:
                                        screenshot_cropped:
                                            type: string
                                        y_offset:
                                            type: integer
                                        observed_at:
                                            type: string
                                        ocr_data:
                                            type: array
                                            items:
                                                type: object
                                                properties:
                                                    text:
                                                        type: string
                                                    x:
                                                        type: integer
                                                    y:
                                                        type: integer
                                                    width:
                                                        type: integer
                                                    height:
                                                        type: integer
                                                    confidence:
                                                        type: number
        400:
            description: A failed response
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
                                example: 'MISSING_PARAMETERS: observer_id, timestamp, ad_id'
    """
    observer_id, timestamp, ad_id = event['ad_params']
    observer = observations_repository.Observer(observer_id)
    rdo_builder = RdoBuilder(observer)
    ocr_data = rdo_builder.get_ocr_data(timestamp, ad_id)
    return {
        'success': True,
        'ocr_data': ocr_data
    }
    
@route('ads/{observer_id}/{timestamp}.{ad_id}/rdo/dimensions', 'GET')
@use(authenticate)
@use(parse_ad_params)
def get_ad_dimensions(event, response):
    """Retrieve dimensions for an ad.

    Retrieve the width and height of the specified ad.
    ---
    tags:
        - ads
        - rdo
    parameters:
        - in: path
          name: observer_id
          required: true
          schema:
              type: string
        - in: path
          name: timestamp
          required: true
          schema:
              type: string
        - in: path
          name: ad_id
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
                            dimensions:
                                type: object
                                properties:
                                    w:
                                        type: integer
                                    h:
                                        type: integer
        400:
            description: A failed response
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
                                example: 'MISSING_PARAMETERS: observer_id, timestamp, ad_id'
    """
    observer_id, timestamp, ad_id = event['ad_params']
    observer = observations_repository.Observer(observer_id)
    rdo_builder = RdoBuilder(observer)
    dimensions = rdo_builder.get_ad_dimensions(timestamp, ad_id)
    return {
        'success': True,
        'dimensions': dimensions
    }


@route('ads/{observer_id}/{timestamp}.{ad_id}/rdo/candidates', 'GET')
@use(authenticate)
@use(parse_ad_params)
def get_meta_candidates(event, response):
    """Retrieve meta candidates for an ad.

    Retrieve meta candidates for the specified ad, including media paths and rankings.
    ---
    tags:
        - ads
        - rdo
    parameters:
        - in: path
          name: observer_id
          required: true
          schema:
              type: string
        - in: path
          name: timestamp
          required: true
          schema:
              type: string
        - in: path
          name: ad_id
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
                            candidates:
                                type: array
                                items:
                                    type: object
                            media_paths:
                                type: object
                                additionalProperties:
                                    type: string
                            rankings:
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
                                example: False
                            comment:
                                type: string
                                example: 'MISSING_PARAMETERS: observer_id, timestamp, ad_id'
    """
    observer_id, timestamp, ad_id = event['ad_params']
    observer = observations_repository.Observer(observer_id)
    rdo_builder = RdoBuilder(observer)
    candidates = rdo_builder.get_candidates(timestamp, ad_id)
    media_paths = rdo_builder.get_downloaded_media(timestamp, ad_id)
    rankings = rdo_builder.get_rankings(timestamp, ad_id)
    return {
        'success': True,
        'candidates': candidates,
        'media_paths': media_paths,
        'rankings': rankings
    }
    
@route('ads/query', 'POST')
@use(authenticate)
def query(event, response):
    """Query ads based on specified criteria.

    Perform a query on ads using the specified criteria and return the matching ad paths.
    ---
    tags:
        - ads
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        method:
                            type: string
                            example: OR
                        args:
                            type: array
                            items:
                                type: object
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
                            result:
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
                                example: False
                            comment:
                                type: string
                                example: 'INVALID_QUERY'
    """
    # Example query:
    # {
    #     "method": "OR",
    #     "args": [
    #     {
    #         "method": "AND",
    #         "args": [
    #         {
    #             "method": "MATCH",
    #             "args": ["cats"]
    #         },
    #         {
    #             "method": "MATCH",
    #             "args": ["dogs"]
    #         }
    #         ]
    #     },
    #     {
    #         "method": "MATCH",
    #         "args": ["bird"]
    #     }
    #     ]
    # }
    query_dict = event['body']
    ad_query = AdQuery()
    try:
        result = ad_query.query(query_dict) # List of ad paths that satisfy the query
        return {
            'success': True,
            'result': result
        }
    except Exception as e:
        return response.status(400).json({
            'success': False,
            'comment': f"Error executing query: {str(e)}"
        })