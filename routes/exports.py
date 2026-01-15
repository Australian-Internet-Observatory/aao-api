"""
Export routes for the Australian Ad Observatory API.

Provides endpoints for creating, listing, retrieving, deleting, 
and sharing export jobs.
"""
import json
import logging
import os
from datetime import datetime
from routes import route
from middlewares.authenticate import authenticate
from utils import Response, use
from utils.sqs_client import SQSClient
from utils.swift_client import SwiftClient
from db.shared_repositories import (
    exports_repository,
    shared_exports_repository,
    exportable_fields_repository,
    export_fields_repository,
    users_repository
)
from models.export import ExportStatus

logger = logging.getLogger(__name__)

# Maximum retries for export jobs (from config or default)
MAX_RETRIES = 3


def export_to_dict(export, shared_user_ids: list[str] = None, field_paths: list[str] = None) -> dict:
    """Convert an export entity to a dictionary response.

    If `export.object_location` is set, attempt to convert it into a
    temporary public URL using `SwiftClient.get_temp_url`. If parsing or
    generating the temp URL fails, fall back to the stored `object_location`.
    """
    # Default to the raw stored object location
    url = export.object_location

    if url:
        print("Generating temp URL for export:", export.id)
        container = os.getenv('EXPORTS_BUCKET_NAME')
        object_name = url

        try:
            sc = SwiftClient()
            url = sc.get_temp_url(container, object_name)
            print("Generated temp URL:", url)
        except Exception as e:
            logger.warning(f"Failed to generate temp URL for export {export.id}: {e}")
            url = export.object_location
    
    result = {
        "export_id": export.id,
        "creator_id": export.creator_id,
        "export_parameters": {
            "query": json.loads(export.query_string) if export.query_string else None,
            "include_images": export.include_images,
            "fields": field_paths or []
        },
        "shared_with": shared_user_ids or [],
        "status": export.status,
        "url": url,
        "created_at": export.created_at.isoformat() if export.created_at else None,
        "updated_at": export.updated_at.isoformat() if export.updated_at else None,
        "started_at": export.started_at.isoformat() if export.started_at else None,
        "completed_at": export.completed_at.isoformat() if export.completed_at else None,
        "message": export.message
    }
    return result


def get_export_field_paths(export_id: str) -> list[str]:
    """Get the field paths for an export."""
    with export_fields_repository.create_session() as ef_session, \
         exportable_fields_repository.create_session() as field_session:
        export_fields = ef_session.get({'export_id': export_id})
        if not export_fields:
            return []
        paths = []
        for ef in export_fields:
            field = field_session.get_first({'id': ef.field_id})
            if field:
                paths.append(field.path)
        return paths


def get_shared_user_ids(export_id: str) -> list[str]:
    """Get the user IDs with whom an export is shared."""
    with shared_exports_repository.create_session() as session:
        shared = session.get({'export_id': export_id})
        if not shared:
            return []
        return [s.user_id for s in shared]


def send_export_to_queue(export_id: str, creator_id: str, export_parameters: dict, attempt: int = 1) -> bool:
    """Send an export job to the SQS queue."""
    try:
        sqs_client = SQSClient()
        message = {
            "export_id": export_id,
            "creator_id": creator_id,
            "export_parameters": export_parameters,
            "attempt": attempt,
            "max_retries": MAX_RETRIES
        }
        sqs_client.send_message(json.dumps(message))
        logger.info(f"Export job {export_id} sent to queue successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to send export job {export_id} to queue: {e}")
        return False
@route('/exports/fields', 'GET')
@use(authenticate)
def list_exportable_fields(event, response: Response, context):
    """List all available exportable fields.

    Returns a list of fields that users can select to include in their exports.
    ---
    tags:
      - exports
    responses:
      200:
        description: List of exportable fields
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                  name:
                    type: string
                  description:
                    type: string
                  path:
                    type: string
                  is_default:
                    type: boolean
    """
    with exportable_fields_repository.create_session() as session:
        fields = session.list()
    
    return [
        {
            "id": f.id,
            "name": f.name,
            "description": f.description,
            "path": f.path,
            "is_default": f.is_default
        }
        for f in fields
    ]


@route('/exports', 'POST')
@use(authenticate)
def create_export(event, response: Response, context):
    """Create a new export job.

    Initiates an asynchronous export job that will be processed by a background worker.
    The export job will be queued and the user can monitor its status.
    ---
    tags:
      - exports
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              export_parameters:
                type: object
                properties:
                  query:
                    type: object
                    description: Query to filter the data to export
                  include_images:
                    type: boolean
                    default: false
                  fields:
                    type: array
                    items:
                      type: string
                    description: List of field paths to include in the export
    responses:
      201:
        description: Export job created successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                export:
                  type: object
      400:
        description: Bad request
      500:
        description: Failed to queue export job
    """
    user = event.get('user')
    
    if not user:
        return response.status(401).json({
            "success": False,
            "comment": "User not authenticated"
        })
    
    creator_id = user.id
    export_params = event.get('body', {})
    
    query = export_params.get('query', {})
    include_images = export_params.get('include_images', False)
    field_paths = export_params.get('fields', [])
    
    # Create the export record
    export_data = {
        'creator_id': creator_id,
        'include_images': include_images,
        'query_string': json.dumps(query) if query else None,
        'status': ExportStatus.PENDING.value,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    with exports_repository.create_session() as session:
        export_record = session.create(export_data)
        export_id = export_record['id']
    
    # Build the export parameters for the queue message
    queue_params = {
        "query": query,
        "include_images": include_images,
        "fields": field_paths
    }
    
    # Send to SQS queue
    if not send_export_to_queue(export_id, creator_id, queue_params):
        # Update status to failed if queue send fails
        with exports_repository.create_session() as session:
            export_record['status'] = ExportStatus.FAILED.value
            export_record['message'] = "Failed to queue export job"
            export_record['updated_at'] = datetime.utcnow()
            session.update(export_record)
        
        return response.status(500).json({
            "success": False,
            "comment": "Failed to queue export job"
        })
    
    # Retrieve the created export for response
    with exports_repository.create_session() as session:
        export = session.get_first({'id': export_id})
    
    return response.status(201).json({
        "success": True,
        "export": export_to_dict(export, [], field_paths)
    })


@route('/exports', 'GET')
@use(authenticate)
def list_exports(event, response: Response, context):
    """List all exports for a user.

    Returns exports created by the user or shared with them.
    ---
    tags:
      - exports
    parameters:
      - name: user_id
        in: query
        schema:
          type: string
        description: Optional user ID to filter exports. If not provided, returns exports for the authenticated user.
    responses:
      200:
        description: List of export jobs
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
    """
    user = event.get('user')
    
    if not user:
        return response.status(401).json({
            "success": False,
            "comment": "User not authenticated"
        })
    
    authenticated_user_id = user.id
    
    # Get user_id from query params, default to authenticated user
    query_params = event.get('queryStringParameters') or {}
    target_user_id = query_params.get('user_id', authenticated_user_id)
    
    # Users can only see their own exports unless they're admin
    if target_user_id != authenticated_user_id and user.role != 'admin':
        return response.status(403).json({
            "success": False,
            "comment": "UNAUTHORISED"
        })
    
    exports_list = []
    seen_export_ids = set()
    
    # Get exports created by the user
    with exports_repository.create_session() as session:
        created_exports = session.get({'creator_id': target_user_id})
        if created_exports:
            for export in created_exports:
                if export.id not in seen_export_ids:
                    seen_export_ids.add(export.id)
                    field_paths = get_export_field_paths(export.id)
                    shared_with = get_shared_user_ids(export.id)
                    exports_list.append(export_to_dict(export, shared_with, field_paths))
    
    # Get exports shared with the user
    with shared_exports_repository.create_session() as shared_session, \
         exports_repository.create_session() as export_session:
        shared_exports = shared_session.get({'user_id': target_user_id})
        if shared_exports:
            for shared in shared_exports:
                if shared.export_id not in seen_export_ids:
                    seen_export_ids.add(shared.export_id)
                    export = export_session.get_first({'id': shared.export_id})
                    if export:
                        field_paths = get_export_field_paths(export.id)
                        shared_with = get_shared_user_ids(export.id)
                        exports_list.append(export_to_dict(export, shared_with, field_paths))
    
    return exports_list


@route('/exports/{export_id}', 'GET')
@use(authenticate)
def get_export(event, response: Response, context):
    """Get a specific export job by ID.

    Returns detailed information about an export job including status, parameters, and download URL.
    ---
    tags:
      - exports
    parameters:
      - name: export_id
        in: path
        required: true
        schema:
          type: string
    responses:
      200:
        description: Export job details
        content:
          application/json:
            schema:
              type: object
      403:
        description: Unauthorized access
      404:
        description: Export not found
    """
    user = event.get('user')
    
    if not user:
        return response.status(401).json({
            "success": False,
            "comment": "User not authenticated"
        })
    
    user_id = user.id
    export_id = event['pathParameters']['export_id']
    
    with exports_repository.create_session() as session:
        export = session.get_first({'id': export_id})
    
    if not export:
        return response.status(404).json({
            "success": False,
            "comment": "Export not found"
        })
    
    # Check if user has access (creator or shared with)
    is_creator = export.creator_id == user_id
    is_admin = user.role == 'admin'
    shared_with = get_shared_user_ids(export_id)
    is_shared = user_id in shared_with
    
    if not (is_creator or is_admin or is_shared):
        return response.status(403).json({
            "success": False,
            "comment": "UNAUTHORISED"
        })
    
    field_paths = get_export_field_paths(export_id)
    return export_to_dict(export, shared_with, field_paths)


@route('/exports/{export_id}', 'DELETE')
@use(authenticate)
def delete_export(event, response: Response, context):
    """Delete an export job.

    Deletes the export job and its associated files. Only the creator or admin can delete an export.
    ---
    tags:
      - exports
    parameters:
      - name: export_id
        in: path
        required: true
        schema:
          type: string
    responses:
      200:
        description: Export deleted successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
      403:
        description: Unauthorized access
      404:
        description: Export not found
    """
    user = event.get('user')
    
    if not user:
        return response.status(401).json({
            "success": False,
            "comment": "User not authenticated"
        })
    
    user_id = user.id
    export_id = event['pathParameters']['export_id']
    
    with exports_repository.create_session() as session:
        export = session.get_first({'id': export_id})
    
    if not export:
        return response.status(404).json({
            "success": False,
            "comment": "Export not found"
        })
    
    # Only creator or admin can delete
    is_creator = export.creator_id == user_id
    is_admin = user.role == 'admin'
    
    if not (is_creator or is_admin):
        return response.status(403).json({
            "success": False,
            "comment": "UNAUTHORISED"
        })
    
    # Delete shared exports first (due to foreign key constraint)
    with shared_exports_repository.create_session() as session:
        shared = session.get({'export_id': export_id})
        if shared:
            for s in shared:
                session.delete({'export_id': export_id, 'user_id': s.user_id})
    
    # Delete export fields
    with export_fields_repository.create_session() as session:
        fields = session.get({'export_id': export_id})
        if fields:
            for f in fields:
                session.delete({'export_id': export_id, 'field_id': f.field_id})
    
    # Delete the export
    with exports_repository.create_session() as session:
        session.delete({'id': export_id})
    
    return {
        "success": True,
        "comment": "Export deleted successfully"
    }


@route('/exports/{export_id}/share', 'POST')
@use(authenticate)
def share_export(event, response: Response, context):
    """Share an export with other users.

    Adds users to the export's access list. Only the creator or admin can share.
    ---
    tags:
      - exports
    parameters:
      - name: export_id
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
              user_ids:
                type: array
                items:
                  type: string
                description: List of user IDs to share with
    responses:
      200:
        description: Export shared successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                shared_with:
                  type: array
                  items:
                    type: string
      400:
        description: Bad request
      403:
        description: Unauthorized access
      404:
        description: Export not found
    """
    user = event.get('user')
    
    if not user:
        return response.status(401).json({
            "success": False,
            "comment": "User not authenticated"
        })
    
    user_id = user.id
    export_id = event['pathParameters']['export_id']
    data = event.get('body', {})
    user_ids_to_share = data.get('user_ids', [])
    
    if not user_ids_to_share:
        return response.status(400).json({
            "success": False,
            "comment": "No user IDs provided"
        })
    
    with exports_repository.create_session() as session:
        export = session.get_first({'id': export_id})
    
    if not export:
        return response.status(404).json({
            "success": False,
            "comment": "Export not found"
        })
    
    # Only creator or admin can share
    is_creator = export.creator_id == user_id
    is_admin = user.role == 'admin'
    
    if not (is_creator or is_admin):
        return response.status(403).json({
            "success": False,
            "comment": "UNAUTHORISED"
        })
    
    # Verify users exist and add to shared list
    added_users = []
    with users_repository.create_session() as user_session, \
         shared_exports_repository.create_session() as shared_session:
        for target_user_id in user_ids_to_share:
            # Check if user exists
            target_user = user_session.get_first({'id': target_user_id})
            if not target_user:
                continue
            
            # Check if already shared
            existing = shared_session.get_first({
                'export_id': export_id,
                'user_id': target_user_id
            })
            if existing:
                added_users.append(target_user_id)
                continue
            
            # Add share
            try:
                shared_session.create({
                    'export_id': export_id,
                    'user_id': target_user_id
                })
                added_users.append(target_user_id)
            except Exception as e:
                logger.error(f"Failed to share export {export_id} with user {target_user_id}: {e}")
    
    return {
        "success": True,
        "shared_with": get_shared_user_ids(export_id)
    }


@route('/exports/{export_id}/unshare', 'POST')
@use(authenticate)
def unshare_export(event, response: Response, context):
    """Remove users from an export's access list.

    Removes users from the export's shared access. Only the creator or admin can unshare.
    ---
    tags:
      - exports
    parameters:
      - name: export_id
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
              user_ids:
                type: array
                items:
                  type: string
                description: List of user IDs to remove from access
    responses:
      200:
        description: Users removed from export successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                shared_with:
                  type: array
                  items:
                    type: string
      400:
        description: Bad request
      403:
        description: Unauthorized access
      404:
        description: Export not found
    """
    user = event.get('user')
    
    if not user:
        return response.status(401).json({
            "success": False,
            "comment": "User not authenticated"
        })
    
    user_id = user.id
    export_id = event['pathParameters']['export_id']
    data = event.get('body', {})
    user_ids_to_remove = data.get('user_ids', [])
    
    if not user_ids_to_remove:
        return response.status(400).json({
            "success": False,
            "comment": "No user IDs provided"
        })
    
    with exports_repository.create_session() as session:
        export = session.get_first({'id': export_id})
    
    if not export:
        return response.status(404).json({
            "success": False,
            "comment": "Export not found"
        })
    
    # Only creator or admin can unshare
    is_creator = export.creator_id == user_id
    is_admin = user.role == 'admin'
    
    if not (is_creator or is_admin):
        return response.status(403).json({
            "success": False,
            "comment": "UNAUTHORISED"
        })
    
    # Remove from shared list
    with shared_exports_repository.create_session() as session:
        for target_user_id in user_ids_to_remove:
            try:
                session.delete({
                    'export_id': export_id,
                    'user_id': target_user_id
                })
            except Exception as e:
                logger.error(f"Failed to unshare export {export_id} from user {target_user_id}: {e}")
    
    return {
        "success": True,
        "shared_with": get_shared_user_ids(export_id)
    }