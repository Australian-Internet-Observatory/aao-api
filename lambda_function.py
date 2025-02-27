import datetime
import traceback
import dateutil.tz
from middlewares import parse_body
from middlewares.authenticate import authenticate
from routes import parse_path_parameters, route
from utils import use
import base64
import json
from routes import routes
import utils.observations_repository as observations_repository


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

@route('/hello/{user_id}', 'GET')
def hello(event):
    user_id = event['pathParameters']['user_id']
    return {'message': f'Hello, {user_id}!'}

def lambda_handler(event_raw, context):
    try:
        event, response, context = parse_body(event_raw, context, None)
        
        path = event['path']
        method = event['httpMethod']
        if not path.startswith('/'):
            path = f'/{path}'
        if path.endswith('/'):
            path = path[:-1]
        
        route, path_params = parse_path_parameters(path)
        print(f'Route: {route}')
        print(f'Path params: {path_params}')
        print(f'Method: {method}')
        if path_params is not None and len(path_params) > 0:
            event['pathParameters'] = path_params
        
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
                'error': f'No route found for "{path}" with method "{method}"'
            })
        }
    except Exception as e:
        print(traceback.format_exc())
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
        'path': 'hello/test',
        'httpMethod': 'GET'
    }
    context = {}
    print(json.dumps(lambda_handler(event, context), indent=2))