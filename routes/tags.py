from db.clients.rds_storage_client import RdsStorageClient
from db.repository import Repository
from middlewares.authenticate import authenticate
from models.ad_tag import AdTag, AdTagORM
from models.tag import Tag, TagORM
from routes import route
from utils import Response, use
from db.shared_repositories import tags_repository, applied_tags_repository as ads_tags_repository


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
    with tags_repository.create_session() as session:
        result = session.create(tag)
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
    with tags_repository.create_session() as session:
        tags = session.list()
    return [tag.model_dump() for tag in tags]

@route('/tags/{tag_id}', 'GET')
@use(authenticate)
def get_tag(event, response: Response, context):
    """Retrieve a tag by ID.
    ---
    tags:
      - tags
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
    with tags_repository.create_session() as session:
        tag = session.get_first({ 'id': tag_id })
        if tag is None:
            return response.status(404).json({'success': False, 'comment': 'Tag not found'})
    return tag.model_dump_json()

@route('/tags/{tag_id}', 'PUT')
@use(authenticate)
def update_tag(event, response: Response, context):
    """Update an existing tag.
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
      200:
        description: Tag updated successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: True
                tag:
                  $ref: '#/components/schemas/Tag'
      404:
        description: Tag not found
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
                  example: 'Tag not found'
    """
    tag_id = event['pathParameters']['tag_id']
    data = event['body']
    with tags_repository.create_session() as session:
        tag = session.get_first({ 'id': tag_id })
        if tag is None:
            return response.status(404).json({'success': False, 'comment': 'Tag not found'})
        
        tag.name = data['name']
        tag.description = data['description']
        tag.hex = data['hex']
        session.update(tag)
    return response.status(200).json({
        'success': True,
        'tag': tag.model_dump()
    })

@route('/tags/{tag_id}', 'DELETE')
@use(authenticate)
def delete_tag(event, response: Response, context):
    """Delete a tag by ID.
    ---
    tags:
      - tags
    responses:
      200:
        description: Tag deleted successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: True
      404:
        description: Tag not found
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
                  example: 'Tag not found'
    """
    tag_id = event['pathParameters']['tag_id']
    with tags_repository.create_session() as session:
        tag = session.get_first({ 'id': tag_id })
        if tag is None:
            return response.status(404).json({'success': False, 'comment': 'Tag not found'})
        session.delete({ 'id': tag_id })
    return response.json({'success': True})
    
@route('ads/{observer_id}/{timestamp}.{ad_id}/tags', 'GET')
@use(authenticate)
def get_tags_for_ad(event, response: Response, context):
    """Retrieve all tag IDs for an ad.
    ---
    tags:
      - ads/tags
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
    ad_id = event['pathParameters']['ad_id']

    try:
        with ads_tags_repository.create_session() as session:
            tags: list[AdTag] = session.get({ "observation_id": ad_id })
            tag_ids = [tag.tag_id for tag in tags]
        
        return {'success': True, 'tag_ids': tag_ids}
    except Exception as e:
        return response.status(400).json({'success': False, 'comment': 'ERROR_RETRIEVING_TAG_IDS'})

@route('ads/{observer_id}/{timestamp}.{ad_id}/tags', 'PUT')
@use(authenticate)
def update_tags_for_ad(event, response: Response, context):
    """Update tag IDs for an ad.
    ---
    tags:
      - ads/tags
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
        # Delete existing records to avoid duplicates
        with ads_tags_repository.create_session() as session:
            try:
                session.delete({ 'observation_id': ad_id })
            except Exception as e:
                # If no records found, ignore the error - we will create new ones
                if "No objects found" in str(e):
                    pass
            
            if not data['tag_ids']:
                return {'success': True}
            
            # If there are tags, create new records
            for tag_id in data['tag_ids']:
                ad_tag = AdTag(
                    observation_id=ad_id,
                    tag_id=tag_id
                )
                session.create_or_update(ad_tag)
        return {'success': True}
    except Exception as e:
        response.status(400).json({'success': False, 'comment': 'ERROR_UPDATING_TAG_IDS', 'error': str(e)})
        return