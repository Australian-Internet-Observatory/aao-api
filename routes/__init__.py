from functools import wraps
from utils import use
import inspect
import typing
import re

routes = {}

HttpMethod = typing.Literal['GET', 'POST', 'PUT', 'DELETE', 'PATCH']

def route(action: str, method: HttpMethod ='GET'):
    def decorator(func):
        @wraps(func) # Preserve the function metadata (name, docstring, etc.)
        @use(lambda event, response, context: (event, response, context))
        def inner(event, response, context=None):
            num_args = len(inspect.signature(func).parameters)
            args = (event, response, context)
            results = func(*args[:num_args])
            if results is None:
                return event, response, context
            is_tuple = type(results) == tuple
            if len(results) == 3 and is_tuple:
                event, response, context = results
            if not is_tuple:
                data = results
                if type(data) in [dict, str, list]:
                    response.json(data)
                # if type(data) == dict:
                #     response.json(data)
                # if type(data) == str:
                #     response.json(data)
                # if type(data) == list:
                #     response.json(data)
            # return func(event, response, context)
            return event, response, context
        # Ensure the route starts with a forward slash and does not end with one
        formatted_route = action if action.startswith("/") else f"/{action}"
        formatted_route = formatted_route[:-1] if formatted_route.endswith("/") else formatted_route
        if formatted_route not in routes:
            routes[formatted_route] = {}
        routes[formatted_route][method.upper()] = inner
        return inner
    return decorator

def get_path_param_keys(route: str) -> list[str]:
    """Get the keys of the path parameters in a route.
    
    Example:
    
    Assuming a route with the path pattern '/users/{user_id}/profile', the following code:
    
    ```python
    keys = get_path_param_keys('/users/{user_id}/profile')
    print(keys)
    ```
    
    Would output:
    
    ```python
    ['user_id']
    ```

    Args:
        route (str): The route to extract the path parameters from.

    Returns:
        list[str]: The keys of the path parameters in the route.
    """
    # Use regex to find all fields between curly braces
    return re.findall(r'{(.*?)}', route)

def parse_path_parameters(path: str) -> tuple[str, dict]:
    """Find the route associated with a path pattern and extract the path parameters.
    Raises a KeyError if the path does not match any route.
    
    If a static route is found, the path parameters will be an empty dictionary.
    
    Example:
    
    Assuming a route with the path pattern '/users/{user_id}/profile', the following code:
    
    ```
    path, params = parse_path_parameters('/users/123/profile')
    print(path, params)
    ```
    
    Would output:
    
    ```
    /users/{user_id}/profile {'user_id': '123'}
    ```

    Args:
        path (str): The url path to look up.

    Returns:
        tuple[str, dict]: The route pattern and the extracted path parameters from the url.
    """
    for candidate, _ in routes.items():
        # If an exact match is found -> the route is static and has no parameters
        if candidate == path:
            return candidate, {}
    
    # Otherwise, check for a dynamic route
    for candidate, methods in routes.items():
        route_parts = candidate.split('/')
        path_parts = path.split('/')
        if len(route_parts) != len(path_parts):
            continue
        params = {}
        path_param_keys = get_path_param_keys(candidate)
        
        # Replace all {param} with (.*?) regex pattern to find the parameter values
        escaped_route = re.escape(candidate)
        escaped_route = re.sub(r'\\{.*?\\}', r'(.*?)', escaped_route)
        parse_regex = f"^{escaped_route}$"
        matches = re.match(parse_regex, path)
        if matches is None:
            continue
        for i, key in enumerate(path_param_keys):
            params[key] = matches.group(i + 1)
        return candidate, params
    raise KeyError(f'No route found for path: {path}')

# Declare all routes here - won't work without the imports
from . import auth
from . import users
from . import ads
from . import observers
from . import ad_attributes
from . import media
from . import guest