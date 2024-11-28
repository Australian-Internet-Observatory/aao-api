from functools import wraps
from utils import use
import inspect

routes = {}

def route(action):
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
                if type(data) == dict:
                    response.json(data)
                if type(data) == str:
                    response.json({
                        'message': data
                    })
                if type(data) == list:
                    response.json({
                        'data': data
                    })
            # return func(event, response, context)
            return event, response, context
        routes[action] = inner
        return inner
    return decorator

# Declare all routes here
from . import auth
from . import users
from . import ad_attributes