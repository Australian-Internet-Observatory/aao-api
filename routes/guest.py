from routes import route
from utils import use
import utils.metadata_repository as metadata
from middlewares.authorise import authorise, Role
from middlewares.authenticate import authenticate
from utils.jwt import create_token
import time
import json

SESSION_FOLDER_PREFIX = 'guest-sessions'

@route('/guest/sessions', 'POST')
@use(authenticate)
@use(authorise(Role.ADMIN, Role.USER))
def create_session(event, response, context):
    """Create a guest session.
    ---
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              key:
                type: string
                description: A unique identifier for the session.
              expiration_time:
                type: integer
                description: The time in seconds until the session expires.
              description:
                type: string
                description: A description of the session.
    responses:
      200:
        description: A JSON object containing the session token
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                token:
                  type: string
              example:
                success: true
                token: "jwt_token"
      400:
        description: A JSON object containing an error message
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                comment:
                  type: string
              example:
                success: false
                comment: "Error message"
    """
    body = event['body']
    key = body.get('key')
    expiration_time = body.get('expiration_time')
    description = body.get('description', None)

    if not key or not expiration_time:
        response.status(400).json({
            "success": False,
            "comment": "Missing required fields"
        })
        return event, response, context

    expiration_timestamp = int(time.time()) + expiration_time
    session_data = {
        "exp": expiration_timestamp,
        "username": key,
        "role": "guest",
        "enabled": True,
        "full_name": "Guest",
        "description": description
    }

    session_file_key = f"{SESSION_FOLDER_PREFIX}/{key}.json"
    metadata.put_object(session_file_key, json.dumps(session_data))

    token = create_token(session_data)
    response.json({
        "success": True,
        "token": token
    })
    return event, response, context


@route('/guest/sessions', 'GET')
@use(authenticate)
@use(authorise(Role.ADMIN, Role.USER))
def list_sessions(event, response, context):
    """List all guest sessions.
    ---
    responses:
      200:
        description: A JSON array containing session data
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  key:
                    type: string
                  data:
                    type: object
              example:
                - key: "session_key"
                  data: { "exp": 1234567890, "username": "session_key", "role": "guest", "enabled": True, "full_name": "Guest", "description": "Session description" }
    """
    sessions = []
    for key in metadata.list_objects(SESSION_FOLDER_PREFIX):
        session_data = json.loads(metadata.get_object(key))
        sessions.append({
            "key": key.split('/')[-1].split('.')[0],
            "data": session_data
        })

    response.json(sessions)
    return event, response, context

@route('/guest/sessions/{key}', 'GET')
@use(authenticate)
@use(authorise(Role.ADMIN, Role.USER))
def get_session(event, response, context):
    """Retrieve a guest session.
    ---
    parameters:
      - name: key
        in: path
        required: true
        schema:
          type: string
        description: The key of the session.
    responses:
      200:
        description: A JSON object containing the session token
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                token:
                  type: string
              example:
                success: true
                token: "jwt_token"
      404:
        description: A JSON object containing an error message
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                comment:
                  type: string
              example:
                success: false
                comment: "Session not found"
    """
    key = event['pathParameters']['key']
    session_file_key = f"{SESSION_FOLDER_PREFIX}/{key}.json"

    try:
        session_data = json.loads(metadata.get_object(session_file_key))
    except metadata.s3.exceptions.NoSuchKey:
        response.status(404).json({
            "success": False,
            "comment": "Session not found"
        })
        return event, response, context

    token = create_token(session_data)
    response.json({
        "success": True,
        "token": token
    })
    return event, response, context

@route('/guest/sessions/{key}', 'DELETE')
@use(authenticate)
@use(authorise(Role.ADMIN, Role.USER))
def delete_session(event, response, context):
    """Delete a guest session.
    ---
    parameters:
      - name: key
        in: path
        required: true
        schema:
          type: string
        description: The key of the session.
    responses:
      200:
        description: A JSON object indicating success
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                comment:
                  type: string
              example:
                success: true
                comment: "Session deleted"
      404:
        description: A JSON object containing an error message
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                comment:
                  type: string
              example:
                success: false
                comment: "Session not found"
    """
    key = event['pathParameters']['key']
    session_file_key = f"{SESSION_FOLDER_PREFIX}/{key}.json"

    try:
        metadata.delete_object(session_file_key)
    except metadata.s3.exceptions.NoSuchKey:
        response.status(404).json({
            "success": False,
            "comment": "Session not found"
        })
        return event, response, context

    response.json({
        "success": True,
        "comment": "Session deleted"
    })
    return event, response, context

@route('/guest/sessions/{key}', 'PATCH')
@use(authenticate)
@use(authorise(Role.ADMIN, Role.USER))
def update_session(event, response, context):
    """Update a guest session.
    ---
    parameters:
      - name: key
        in: path
        required: true
        schema:
          type: string
        description: The key of the session.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              description:
                type: string
                description: A new description for the session.
              expiration_time:
                type: integer
                description: A new expiration time for the session in seconds.
    responses:
      200:
        description: A JSON object indicating success
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                comment:
                  type: string
              example:
                success: true
                comment: "Session updated"
      404:
        description: A JSON object containing an error message
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                comment:
                  type: string
              example:
                success: false
                comment: "Session not found"
    """
    key = event['pathParameters']['key']
    body = event['body']
    description = body.get('description', None)
    expiration_time = body.get('expiration_time', None)

    session_file_key = f"{SESSION_FOLDER_PREFIX}/{key}.json"

    try:
        session_data = json.loads(metadata.get_object(session_file_key))
    except metadata.s3.exceptions.NoSuchKey:
        response.status(404).json({
            "success": False,
            "comment": "Session not found"
        })
        return event, response, context

    if description:
        session_data['description'] = description
    if expiration_time:
        session_data['exp'] = int(time.time()) + expiration_time

    metadata.put_object(session_file_key, json.dumps(session_data))

    response.json({
        "success": True,
        "comment": "Session updated"
    })
    return event, response, context