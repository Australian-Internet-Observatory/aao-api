from datetime import datetime
from routes import route
from middlewares.authorise import Role, authorise
from middlewares.authenticate import authenticate
from utils import use, jwt, Response
import hashlib
import boto3
import json
import utils.metadata_repository as metadata
from models.project import Project, TeamMember, Cell

from configparser import ConfigParser
config = ConfigParser()
config.read('config.ini')

session = boto3.Session(
    aws_access_key_id=config['AWS']['ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS']['SECRET_ACCESS_KEY'],
    region_name='ap-southeast-2'
)

PROJECTS_FOLDER_PREFIX = 'projects'

def get_all_projects():
    projects = {}
    for project_id in metadata.list_objects(PROJECTS_FOLDER_PREFIX):
        project_data = metadata.get_object(f"{PROJECTS_FOLDER_PREFIX}/{project_id}")
        project = json.loads(project_data)
        projects[project_id] = project
    return projects

@route('/projects', 'POST')
@use(authenticate)
def create_project(event, response, context):
    """Create a new project.
    ---
    tags:
      - projects
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
    responses:
      201:
        description: Project created successfully
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Project'
    """
    data = event['body']
    project_id = hashlib.sha256(f"{data['name']}{datetime.now()}".encode()).hexdigest()
    project = Project(
        id=project_id,
        name=data['name'],
        description=data['description'],
        ownerId=event['user']['username'],
        team=[{
                'username': event['user']['username'],
                'role': 'admin'
            }],
        cells=[]
    )
    metadata.put_object(f"{PROJECTS_FOLDER_PREFIX}/{project_id}.json", json.dumps(project.__dict__))
    response.status(201)
    return project.__dict__

@route('/projects', 'GET')
@use(authenticate)
def list_projects(event, response, context):
    """List all projects where the user is a part of (either owner, or if the user is an admin, all projects).
    ---
    tags:
      - projects
    responses:
      200:
        description: List of projects
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/Project'
    """
    user = event['user']
    user_projects = []
    for project_id in metadata.list_objects(PROJECTS_FOLDER_PREFIX):
        project_data = metadata.get_object(f"{PROJECTS_FOLDER_PREFIX}/{project_id}")
        project = json.loads(project_data)
        if project['ownerId'] == user['username'] or user['role'] == 'admin' or any(member['username'] == user['username'] for member in project['team']):
            user_projects.append(project)
    return user_projects

@route('/projects/{project_id}', 'GET')
@use(authenticate)
def get_project(event, response, context):
    """Get a project by ID.
    ---
    tags:
      - projects
    parameters:
      - in: path
        name: project_id
        required: true
        schema:
          type: string
    responses:
      200:
        description: Project retrieved successfully
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Project'
      404:
        description: Project not found
    """
    project_id = event['pathParameters']['project_id']
    project_data = metadata.get_object(f"{PROJECTS_FOLDER_PREFIX}/{project_id}.json")
    if project_data:
        project = json.loads(project_data)
        return project
    else:
        response.status(404).json({'message': 'Project not found'})

@route('/projects/{project_id}', 'PUT')
@use(authenticate)
def update_project(event, response, context):
    """Update a project by ID.
    ---
    tags:
      - projects
    parameters:
      - in: path
        name: project_id
        required: true
        schema:
          type: string
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Project'
    responses:
      200:
        description: Project updated successfully
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Project'
      404:
        description: Project not found
    """
    project_id = event['pathParameters']['project_id']
    data = event['body']
    try:
        project = Project(**data)
        metadata.update_object(f"{PROJECTS_FOLDER_PREFIX}/{project_id}.json", json.dumps(project.__dict__))
        return project.__dict__
    except:
        response.status(404).json({'message': 'Project not found'})
    # if project_id in get_all_projects():
    #     project = Project(**data)
    #     metadata.update_object(f"{PROJECTS_FOLDER_PREFIX}/{project_id}.json", json.dumps(project.__dict__))
    #     return project.__dict__
    # else:
    #     response.status(404).json({'message': 'Project not found'})

@route('/projects/{project_id}', 'DELETE')
@use(authenticate)
def delete_project(event, response, context):
    """Delete a project by ID.
    ---
    tags:
      - projects
    parameters:
      - in: path
        name: project_id
        required: true
        schema:
          type: string
    responses:
      204:
        description: Project deleted successfully
      404:
        description: Project not found
    """
    project_id = event['pathParameters']['project_id']
    
    try:
        metadata.delete_object(f"{PROJECTS_FOLDER_PREFIX}/{project_id}.json")
        response.status(204)
    except:
        response.status(404).json({'message': 'Project not found'})