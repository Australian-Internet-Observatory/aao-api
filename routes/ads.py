from dataclasses import dataclass
import datetime
from enum import Enum
import hashlib
import json
import math

import dateutil.tz
from db.clients.s3_storage_client import S3StorageClient
from db.repository import Repository
from enricher import RdoBuilder
from middlewares.authenticate import authenticate
from models.ad import Ad
from models.ad_tag import AdTag
from routes import route
from routes.ad_attributes import AD_ATTRIBUTES_PREFIX
import utils.observations_sub_bucket as observations_sub_bucket
from utils import Response, use
# from utils.query import AdQuery
from utils.opensearch import AdQuery
from utils.opensearch.rdo_open_search import AdWithRDO, RdoOpenSearch
import utils.metadata_sub_bucket as metadata
from multiprocessing import Process, Pipe 
from .tags import ads_tags_repository

# try:
#     EXISTING_ATTRIBUTE_OBJECTS = set(metadata.list_objects(AD_ATTRIBUTES_PREFIX))
# except Exception as e:
#     EXISTING_ATTRIBUTE_OBJECTS = None

def parse_ad_path(ad_path):
    """Parse the ad path into its components: observer_id, timestamp, and ad_id."""
    if ad_path is None:
        raise ValueError("ad_path is None")
    [observer_id, _, rest] = [part for part in ad_path.split('/') if part]
    observer_id = observer_id
    parts = rest.split('.')
    if len(parts) < 2:
        raise ValueError(f"Invalid ad path: {ad_path}")
    ad_id = parts[-1]
    timestamp = ".".join(parts[:-1])
    return {
        'observer_id': observer_id,
        'timestamp': timestamp,
        'ad_id': ad_id
    }

class Enricher:
    """Handles the enrichment of ads with metadata and other relevant information."""
    def __init__(self, ad=None):
        if ad is not None:
            self.observer_id = ad.get("observer_id", None)
            self.timestamp = ad.get("timestamp", None)
            self.ad_id = ad.get("ad_id", None)
        
        if hasattr(self, 'observer_id') and self.observer_id is not None:
            self.observer = observations_sub_bucket.Observer(self.observer_id)
        else:
            raise ValueError("observer_id is None")

        self.execution_time_ms = 0
    
    def timeit(func):
        """Decorator to time the execution of a function."""
        def wrapper(self, *args, **kwargs):
            start_at = datetime.datetime.now(tz=dateutil.tz.tzutc())
            result = func(self, *args, **kwargs)
            end_at = datetime.datetime.now(tz=dateutil.tz.tzutc())
            self.execution_time_ms += (end_at - start_at).total_seconds() * 1000
            return result
        return wrapper
    
    @timeit
    def attach_attributes(self, include=None):
        """Fetch the attributes metadata from """
        ad_attributes_path = f'{AD_ATTRIBUTES_PREFIX}/{self.observer_id}_{self.timestamp}.{self.ad_id}.json'
        try:
            # Ignore the ad attributes if the file does not exist
            if include is not None and ad_attributes_path not in include:
                raise ValueError(f"Key {ad_attributes_path} not in include list")
            ad_attributes_data = json.loads(metadata.get_object(ad_attributes_path, include=include).decode('utf-8'))
            self.attributes = ad_attributes_data
        except Exception as e:
            self.attributes = {}
        return self
    
    def attach_tags(self, include=None):
        """Attach tags to the ad."""
        # Fetch the tags for the ad
        try:
            ad_key = f"{self.observer_id}_{self.timestamp}.{self.ad_id}"
            if include is not None and ad_key not in include:
                raise ValueError(f"Key {ad_key} not in include list")
            tags = ads_tags_repository.get(ad_key, AdTag(id=ad_key, tags=[]))
            print(f"Tags for {ad_key}: {tags}")
            self.tags = tags.tags
        except Exception as e:
            print(f"Error fetching tags for {self.observer_id}/{self.timestamp}.{self.ad_id}: {e}")
            self.tags = []
        return self
    
    @timeit
    def attach_rdo(self):
        # Get the RDO for the ad
        rdo = self.observer.get_pre_constructed_rdo(self.timestamp, self.ad_id)
        if rdo is not None:
            self.rdo = rdo
        else:
            self.rdo = {}
        return self
    
    def to_dict(self):
        """Convert the enriched ad to a dictionary."""
        start_at = datetime.datetime.now(tz=dateutil.tz.tzutc())
        data = {
            "observer_id": self.observer_id,
            "ad_id": self.ad_id,
            "timestamp": self.timestamp,
            "metadata": {}
        }
        if hasattr(self, 'attributes'):
            data['metadata']['attributes'] = self.attributes
        if hasattr(self, 'tags'):
            data['metadata']['tags'] = self.tags
        if hasattr(self, 'rdo'):
            data['metadata']['rdo'] = self.rdo
        end_at = datetime.datetime.now(tz=dateutil.tz.tzutc())
        self.execution_time_ms += (end_at - start_at).total_seconds() * 1000
        return data

class BatchEnricher:
    def __init__(self, ads:list[dict]=[], max_workers=128, parallel=False):
        self.parallel = parallel
        self.enrichers = [Enricher(ad) for ad in ads]
        self.max_workers = min(max_workers, len(self.enrichers))
        self.execution_time_ms = 0
    
    def _attach_chunk(self, target, chunk, conn, **kwargs):
        """Attach attributes to a chunk of ads in parallel."""
        for enricher in chunk:
            target(enricher, **kwargs)
            conn.send(enricher)
        conn.send(None)
    
    def attach_enrichment(self, enricher_target, **kwargs):
        chunk_target = lambda chunk, conn: self._attach_chunk(enricher_target, chunk, conn, **kwargs)
        start_at = datetime.datetime.now(tz=dateutil.tz.tzutc())
        if self.parallel:
            # Split the work into chunks equal to the number of workers
            # with at least one enricher per worker
            chunk_size = max(len(self.enrichers) // self.max_workers, 1)
            chunks = [self.enrichers[i:i + chunk_size] for i in range(0, len(self.enrichers), chunk_size)]
            processes = []
            parent_connections = []
            results = []
            
            # Prepare the processes and connections
            for chunk in chunks:
                parent_conn, child_conn = Pipe()
                parent_connections.append(parent_conn)
                process = Process(target=chunk_target, args=(chunk, child_conn))
                processes.append(process)
            
            # Start the processes
            for process in processes:
                process.start()
                
            # Collect the results from each process
            for parent_conn in parent_connections:
                while True:
                    try:
                        # Receive the result from the child process
                        result = parent_conn.recv()
                        # If the result is None, the process has finished (as defined in _attach_attributes_chunk)
                        if result is None:
                            break
                        results.append(result)
                    except EOFError:
                        # If the connection is closed, break the loop
                        break
            # Wait for all processes to finish
            for process in processes:
                process.join()
                
            # Close the connections
            for parent_conn in parent_connections:
                parent_conn.close()
                
            # Update the enrichers with the results
            self.enrichers = results
        else:
            for enricher in self.enrichers:
                enricher_target(enricher, **kwargs)
        end_at = datetime.datetime.now(tz=dateutil.tz.tzutc())
        self.execution_time_ms += (end_at - start_at).total_seconds() * 1000
        return self
        
    def attach_attributes(self):
        existing_attribute_paths = set(metadata.list_objects(AD_ATTRIBUTES_PREFIX))
        enricher_target = lambda enricher: enricher.attach_attributes(include=existing_attribute_paths)
        # chunk_target = lambda chunk, conn: self._attach_chunk(enricher_target, chunk, conn, include=include)
        return self.attach_enrichment(enricher_target)
    
    def attach_tags(self):
        existing_tags = ads_tags_repository.list()
        existing_tags = [f"{tag.id}" for tag in existing_tags]
        print(f"Existing tags: {existing_tags}")
        enricher_target = lambda enricher: enricher.attach_tags(include=existing_tags)
        return self.attach_enrichment(enricher_target)
    
    def attach_rdo(self):
        enricher_target = lambda enricher: enricher.attach_rdo()
        return self.attach_enrichment(enricher_target)
        
    def to_dict(self):
        return [enricher.to_dict() for enricher in self.enrichers]

@route('ads/{observer_id}', 'GET') # get-access-cache?observer_id=5ea80108-154d-4a7f-8189-096c0641cd87
@use(authenticate)
def get_access_cache(event, response):
    """Retrieve the access cache for an observer and the ads that passed RDO construction.

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
                            ads:
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
    observer_data = observations_sub_bucket.read_json_file(f'{observer_id}/quick_access_cache.json')
    if observer_data is None:
        return response.status(404).json({
            'success': False,
            'comment': 'NO_CACHE_FOUND_FOR_OBSERVER'
        })
    
    ads_passed_rdo_constructions = observer_data.get('ads_passed_rdo_construction', [])
    # expanded = [Enricher(ad_path).attach_attributes().to_dict() for ad_path in ad_paths]
    return {
        'success': True,
        'data': observer_data,
        'ads': ads_passed_rdo_constructions,
        # 'expanded': expanded
    }


def get_stiched_frame_from_rdo(observer_id, timestamp, ad_id):
    observer = observations_sub_bucket.Observer(observer_id)
    rdo = observer.get_pre_constructed_rdo(timestamp, ad_id)
    if rdo is None:
        raise Exception(f"RDO not found for {observer_id}/{timestamp}.{ad_id}")
    media: list[str] = rdo['media']
    # temp-v2 is the new version of stitching
    stiched_frames = [frame for frame in media if 'stitching' in frame or 'temp-v2' in frame]
    return stiched_frames

@route('ads/batch', 'POST')
@use(authenticate)
def get_batch_ads(event, response: Response):
    """
    Retrieve metadata associated with a batch of ads.
    
    Given a list of ads in the request body (with observer_id, timestamp and ad_id fields for each ad), as well as a list of metadata types to include, return the metadata for each ad in the list.
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
                        ads:
                            type: array
                            items:
                                type: object
                                properties:
                                    observer_id:
                                        type: string
                                    timestamp:
                                        type: string
                                    ad_id:
                                        type: string
                        metadata_types:
                            type: array
                            items:
                                type: string
                                enum: ['attributes', 'tags', 'rdo']
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
                            ads:
                                type: array
                                items:
                                    type: object
                                    properties:
                                        observer_id:
                                            type: string
                                        timestamp:
                                            type: string
                                        ad_id:
                                            type: string
                                        metadata:
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
                                example: 'Invalid request'
    """
    body = event['body']
    ads = body.get('ads', [])
    metadata_types = body.get('metadata_types', [])
    if not ads or not metadata_types:
        return response.status(400).json({
            'success': False,
            'comment': 'Invalid request, missing ads or metadata_types'
        })
    
    batch_enricher = BatchEnricher(ads, parallel=True)
    if 'attributes' in metadata_types:
        batch_enricher.attach_attributes()
    
    if 'tags' in metadata_types:
        batch_enricher.attach_tags()
    
    if 'rdo' in metadata_types:
        batch_enricher.attach_rdo()
        
    enriched_ads = batch_enricher.to_dict()
    return {
        'success': True,
        'ads': enriched_ads
    }

@route('ads/batch/presign', 'POST')
@use(authenticate)
def get_batch_ads_presign(event, response: Response):
    """
    Attach metadata to a batch of ads and return a presigned URL for the batch.
    
    Behaves like the ads/batch endpoint, but returns a presigned URL for the batch instead of the metadata itself.
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
                        ads:
                            type: array
                            items:
                                type: object
                                properties:
                                    observer_id:
                                        type: string
                                    timestamp:
                                        type: string
                                    ad_id:
                                        type: string
                        metadata_types:
                            type: array
                            items:
                                type: string
                                enum: ['attributes', 'tags', 'rdo']
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
                                example: 'Invalid request'
    """
    body = event['body']
    ads = body.get('ads', [])
    metadata_types = body.get('metadata_types', [])
    if not ads or not metadata_types:
        return response.status(400).json({
            'success': False,
            'comment': 'Invalid request, missing ads or metadata_types'
        })
    
    # Save the enriched ads to a file and return a presigned URL
    username = event.get('user', {}).get('username', None)
    if username is None:
        raise ValueError("user is None")
    
    # Hash the body to create a unique key for the batch to allow for caching
    key = hashlib.sha256(json.dumps({"ads": sorted(ads, key=lambda ad: ad.get('ad_id', None)), "types": sorted(metadata_types)}).encode('utf-8')).hexdigest()
    filename = f'{key}.json'
    path = f'batch_ads/{username}/{filename}'
    
    # Check if the batch already exists in the metadata bucket
    use_cache = 'rdo' in metadata_types
    if use_cache:
        # If the batch already exists, return the presigned URL for the existing batch
        # and skip the enrichment process
        try:
            existing_batch = metadata.get_object(path, read_body=False)
            print(f"Found existing batch: {path}")
        except Exception as e:
            existing_batch = None
            print(f"Batch not found: {path}")
            
        if existing_batch is not None:
            # Only return the presigned URL if the batch is not older than 1 hour
            last_modified = existing_batch['LastModified']
            now = datetime.datetime.now(tz=dateutil.tz.tzutc())
            cache_age = now - last_modified
            if cache_age < datetime.timedelta(hours=1):
                url = metadata.generate_presigned_url(
                    key=path,
                    expiration=3600,
                    prefer_cache=True
                )
                return response.status(200).json({
                    'success': True,
                    'presigned_url': url,
                })
    
    # Enrich then cache the batch
    
    batch_enricher = BatchEnricher(ads, parallel=True)
    if 'attributes' in metadata_types:
        batch_enricher.attach_attributes()
    
    if 'tags' in metadata_types:
        batch_enricher.attach_tags()
    
    if 'rdo' in metadata_types:
        batch_enricher.attach_rdo()
        
    enriched_ads = batch_enricher.to_dict()
    
    metadata.put_object(
        key=path,
        data=json.dumps(enriched_ads).encode('utf-8')
    )
    
    presigned_url = metadata.generate_presigned_url(
        key=path,
        expiration=3600
    )
    
    return {
        'success': True,
        'presigned_url': presigned_url
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
    # # List the frames at the path
    # frames = observations_sub_bucket.list_dir(path)
    # # print(s3.list_dir(f'{observer_id}/temp'))
    # frame_paths = [f'{frame}' for frame in frames]
    frame_paths = get_stiched_frame_from_rdo(observer_id, timestamp, ad_id)
    
    # Generate presigned URLs for each frame
    presigned_urls = []
    image_extensions = ['.jpg', '.jpeg', '.png']
    for frame_path in frame_paths:
        if not any([frame_path.endswith(ext) for ext in image_extensions]):
            continue
        presigned_url = observations_sub_bucket.client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': observations_sub_bucket.MOBILE_OBSERVATIONS_BUCKET,
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
    frames = observations_sub_bucket.list_dir(path)
    print(path)
    # print(s3.list_dir(f'{observer_id}/temp'))
    frame_paths = [f'{frame}' for frame in frames]
    
    # Generate presigned URLs for each frame
    presigned_urls = []
    image_extensions = ['.jpg', '.jpeg', '.png']
    for frame_path in frame_paths:
        if not any([frame_path.endswith(ext) for ext in image_extensions]):
            continue
        presigned_url = observations_sub_bucket.client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': observations_sub_bucket.MOBILE_OBSERVATIONS_BUCKET,
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
    
    Does not run if the ads_stream.json file already exists and not older than 1 hour.
    """
    # Check if the ads_stream.json file exists and is not older than given cache age
    INDEX_FILENAME = 'ads_stream.json'
    index_obj = observations_sub_bucket.try_get_object(key=INDEX_FILENAME)
    if index_obj is not None:
        # Terminate if the file is not older than given cache age
        last_modified = index_obj['LastModified']
        now = datetime.datetime.now(tz=dateutil.tz.tzutc())
        cache_age = now - last_modified
        print(f'Found cache file. Cache age: {cache_age}')
        if cache_age < datetime.timedelta(hours=1):
            return observations_sub_bucket.read_json_file(INDEX_FILENAME)

    # List all observers
    print('Cache expired or not found. Computing ads stream index...')
    observers = observations_sub_bucket.list_dir()
    
    ads_stream_index = {}
    # For each observer, 
    #   read the quick_access_cache.json file and
    #   compute the ads stream index
    for observer_id in observers:
        if observer_id.endswith('/'):
            observer_id = observer_id[:-1]
        observer_data = observations_sub_bucket.read_json_file(f'{observer_id}/quick_access_cache.json')
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
    observations_sub_bucket.client.put_object(
        Bucket=observations_sub_bucket.MOBILE_OBSERVATIONS_BUCKET,
        Key=INDEX_FILENAME,
        Body=json.dumps(ads_stream_index).encode('utf-8')
    )
    return ads_stream_index

@route('ads', 'GET')
@use(authenticate)
def get_ads_stream_index(event, response):
    """Retrieve the ads stream index as a presigned URL and the ads that passed RDO construction.

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
                            ads:
                                type: array
                                items:
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
        presigned_url = observations_sub_bucket.client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': observations_sub_bucket.MOBILE_OBSERVATIONS_BUCKET,
                'Key': INDEX_FILENAME
            }
        )
        index = observations_sub_bucket.read_json_file(INDEX_FILENAME)
        if index is None:
            return response.status(500).json({
                'success': False,
                'comment': 'FAILED_TO_GET_ADS_STREAM_INDEX',
                'error': 'ads_stream.json not found'
            })
        
        ads_passed_rdo_construction = index.get('ads_passed_rdo_construction', [])
        return {
            'success': True,
            'presigned_url': presigned_url,
            'ads': ads_passed_rdo_construction
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

@route('ads/{observer_id}/{timestamp}.{ad_id}/rdo', 'GET')
@use(authenticate)
@use(parse_ad_params)
def get_ad_rdo(event, response):
    """Retrieve the full Rich Data Object for an ad.

    The Rich Data Object (RDO) is a comprehensive data object that includes all the information, including any enrichments, for the specified ad.
    ---
    tags:
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
                                example: True
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
                                example: 'MISSING_PARAMETERS: observer_id, timestamp, ad_id'
    """
    observer_id, timestamp, ad_id = event['ad_params']
    observer = observations_sub_bucket.Observer(observer_id)
    return {
        'success': True,
        'data': observer.get_pre_constructed_rdo(timestamp, ad_id)
    }

@route('ads/{observer_id}/{timestamp}.{ad_id}/rdo/ocr_data', 'GET')
@use(authenticate)
@use(parse_ad_params)
def get_ad_ocr_data(event, response):
    """Retrieve OCR data for an ad, relative to the stitched frames.

    Retrieve OCR data for the specified ad, including text matches and their positions.
    ---
    tags:
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
    observer = observations_sub_bucket.Observer(observer_id)
    rdo_builder = RdoBuilder(observer)
    ocr_data = rdo_builder.get_ocr_data(timestamp, ad_id)
    return {
        'success': True,
        'ocr_data': ocr_data
    }
    
@route('ads/{observer_id}/{timestamp}.{ad_id}/rdo/ocr_data/raw', 'GET')
@use(authenticate)
@use(parse_ad_params)
def get_ad_raw_ocr_data(event, response):
    """Retrieve OCR data for an ad, relative to the raw frames.

    Retrieve raw OCR data for the specified ad, including text matches and their positions relative to the raw frames. This may include personal or irrelevant information.
    ---
    tags:
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
                                        y_source:
                                            type: object
                                            properties:
                                                t:
                                                    type: integer
                                                b:
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
    observer = observations_sub_bucket.Observer(observer_id)
    rdo_builder = RdoBuilder(observer)
    ocr_data = rdo_builder.get_raw_ocr_data(timestamp, ad_id)
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
    observer = observations_sub_bucket.Observer(observer_id)
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
    observer = observations_sub_bucket.Observer(observer_id)
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
    
@route('ads/{observer_id}/{timestamp}.{ad_id}/request_index', 'GET')
@use(parse_ad_params)
def request_index(event, response):
    """Request that a specific ad be indexed for querying. This should be triggered automatically when an ad has been RDO-processed.
    
    This endpoint should not be called manually, but is triggered when the RDO construction is complete for the specified ad.
    ---
    tags:
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
    try:
        ad_with_rdo = AdWithRDO(observer_id, timestamp, ad_id)
        open_search = RdoOpenSearch()
        data = ad_with_rdo.fetch_rdo()
        open_search.put(ad_with_rdo, data)
        return {
            'success': True
        }
    except Exception as e:
        return response.status(400).json({
            'success': False,
            'comment': f"Error indexing ad: {observer_id}/{timestamp}.{ad_id} - {str(e)}"
        })
    
@route('ads/query', 'POST')
@use(authenticate)
def query(event, response):
    """Query ads based on specified criteria and return the matching ad paths and the expanded ads.

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
                            expand:
                                type: array
                                items:
                                    $ref: '#/components/schemas/Ad'
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
    query_dict = event['body']
    print(f"User '{event['user']['username']}' requested ads with query:")
    print(json.dumps(query_dict, indent=4))
    ad_query = AdQuery()
    try:
        # existing_attribute_paths = set(metadata.list_objects(AD_ATTRIBUTES_PREFIX))
        result = ad_query.query(query_dict) # List of ad paths that satisfy the query
        # print("Enriching ads...")
        # ads = [parse_ad_path(ad_path) for ad_path in result]
        # batch_enricher = BatchEnricher(ads=ads, parallel=True)
        # expanded = batch_enricher.attach_attributes(include=existing_attribute_paths).to_dict()
        
        # def parse_expanded_ad(ad):
        #     ad['attributes'] = ad.get('metadata', {}).get('attributes', {})
        #     # Remove the metadata key
        #     ad.pop('metadata', None)
        #     return ad
        
        # print("Enriching ads complete, took", round(batch_enricher.execution_time_ms, 2), "ms")
        return {
            'success': True,
            'result': result,
            'expand': [] # Keeping for legacy type support
            # 'expand': [parse_expanded_ad(ad) for ad in expanded] 
        }
    except Exception as e:
        return response.status(400).json({
            'success': False,
            'comment': f"Error executing query: {str(e)}"
        })