from db.clients.s3_storage_client import S3StorageClient
from db.repository import Repository
from middlewares.authenticate import authenticate
from models.ad_tag import AdTag
from models.tag import Tag
from routes import route
from utils import Response, use
from uuid import uuid4

tags_repository = Repository(
    model=Tag,
    client=S3StorageClient(
        bucket='fta-mobile-observations-holding-bucket',
        prefix='metadata/tags',
        extension='json'
    )
)

ads_tags_repository = Repository(
    model=AdTag,
    client=S3StorageClient(
        bucket='fta-mobile-observations-holding-bucket',
        prefix='metadata/ads_tags',
        extension='json'
    )
)

@route('/tags', 'POST')
@use(authenticate)
def create_tag(event, response: Response, context):
    """Create a new tag.
    ---
    tags:
      - tags
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              name:
                type: string
              description:
                type: string
              hex:
                type: string
    responses:
      201:
        description: Tag created successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                    type: boolean
                tag:
                    $ref: '#/components/schemas/Tag'
    """
    data = event['body']
    tag = {
        "name": data['name'],
        "description": data['description'],
        "hex": data['hex'],
    }
    result = tags_repository.create(tag)
    return response.status(201).json({
        'success': True,
        'tag': result
    })

@route('/tags', 'GET')
@use(authenticate)
def list_tags(event, response: Response, context):
    """List all tags.
    ---
    tags:
      - tags
    responses:
      200:
        description: A list of tags
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/Tag'
    """
    tags = tags_repository.list()
    return [tag.model_dump_json() for tag in tags]

@route('/tags/{tag_id}', 'GET')
@use(authenticate)
def get_tag(event, response: Response, context):
    """Retrieve a tag by ID.
    ---
    tags:
      - tags
    parameters:
      - name: tag_id
        in: path
        required: true
        schema:
          type: string
    responses:
      200:
        description: Tag retrieved successfully
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Tag'
      404:
        description: Tag not found
    """
    tag_id = event['pathParameters']['tag_id']
    tag = tags_repository.get(tag_id)
    if not tag:
        response.status(404).json({'success': False, 'comment': 'Tag not found'})
        return
    return tag.model_dump_json()

@route('/tags/{tag_id}', 'PUT')
@use(authenticate)
def update_tag(event, response: Response, context):
    """Update an existing tag.
    ---
    tags:
      - tags
    parameters:
      - name: tag_id
        in: path
        required: true
        schema:
          type: string
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              name:
                type: string
              description:
                type: string
              hex:
                type: string
    responses:
      200:
        description: Tag updated successfully
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Tag'
      404:
        description: Tag not found
        content:
            
    """
    tag_id = event['pathParameters']['tag_id']
    data = event['body']
    tag = tags_repository.get(tag_id)
    if not tag:
        response.status(404).json({'success': False, 'comment': 'Tag not found'})
        return
    tag.name = data['name']
    tag.description = data['description']
    tag.hex = data['hex']
    tags_repository.update(tag)
    return tag.model_dump_json()

@route('/tags/{tag_id}', 'DELETE')
@use(authenticate)
def delete_tag(event, response: Response, context):
    """Delete a tag by ID.
    ---
    tags:
      - tags
    parameters:
      - name: tag_id
        in: path
        required: true
        schema:
          type: string
    responses:
      204:
        description: Tag deleted successfully
      404:
        description: Tag not found
    """
    tag_id = event['pathParameters']['tag_id']
    tag = tags_repository.get(tag_id)
    if not tag:
        response.status(404).json({'success': False, 'comment': 'Tag not found'})
        return
    tags_repository.delete(tag)
    response.status(204)
    
@route('ads/{observer_id}/{timestamp}.{ad_id}/tags', 'GET')
@use(authenticate)
def get_tags_for_ad(event, response: Response, context):
    """Retrieve all tag IDs for an ad.
    ---
    tags:
      - ads/tags
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
                tag_ids:
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
                  example: 'ERROR_RETRIEVING_TAG_IDS'
    """
    observer_id = event['pathParameters']['observer_id']
    timestamp = event['pathParameters']['timestamp']
    ad_id = event['pathParameters']['ad_id']
    ad_key = f"{observer_id}/{timestamp}.{ad_id}"

    try:
        tags = ads_tags_repository.get(ad_key)
        if not tags:
            return {'success': True, 'tag_ids': []}
        return {'success': True, 'tag_ids': tags.get('tags', [])}
    except Exception as e:
        response.status(400).json({'success': False, 'comment': 'ERROR_RETRIEVING_TAG_IDS'})
        return

@route('ads/{observer_id}/{timestamp}.{ad_id}/tags', 'PUT')
@use(authenticate)
def update_tags_for_ad(event, response: Response, context):
    """Update tag IDs for an ad.
    ---
    tags:
      - ads/tags
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
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              tag_ids:
                type: array
                items:
                  type: string
    responses:
      200:
        description: Tag IDs updated successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: True
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
                  example: 'ERROR_UPDATING_TAG_IDS'
    """
    observer_id = event['pathParameters']['observer_id']
    timestamp = event['pathParameters']['timestamp']
    ad_id = event['pathParameters']['ad_id']
    ad_key = f"{observer_id}_{timestamp}.{ad_id}"
    data = event['body']
    print("Applying to ad:", ad_key, "tags:", data['tag_ids'])

    try:
        # If no tag ids are provided, remove the ad from the repository
        if not data['tag_ids']:
            ads_tags_repository.delete(ads_tags_repository.get(ad_key))
            return {'success': True}
        
        # Otherwise, create or update the ad with the provided tag ids
        ads_tags_repository.create_or_update({
            'id': ad_key,
            'tags': data['tag_ids']
        })
        return {'success': True}
    except Exception as e:
        response.status(400).json({'success': False, 'comment': 'ERROR_UPDATING_TAG_IDS', 'error': str(e)})
        return