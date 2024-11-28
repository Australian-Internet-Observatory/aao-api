from functools import wraps
import json
import inspect

class Response:
    def __init__(self):
        self.body = {}
        self.terminated = False
        self.logs = []
        
    def status(self, code):
        self.body = {
            'statusCode': code
        }
        self.terminated = True
        return self
    
    def json(self, body):
        self.body = {
            'statusCode': self.body.get('statusCode', 200),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'isBase64Encoded': False,
            'body': json.dumps(body)
        }
        self.terminated = True
    
    def log(self, message):
        self.logs.append(message)
        return self

def use(middleware):
    """Apply a middleware to a function to modify the event and context before the function is executed. Any documentation in the middleware will be appended to the function's documentation.

    Args:
        middleware (function): The middleware function to apply.
    """
    def decorator(func):
        """Decorator function to apply the middleware to the function.

        Args:
            func (function): The function to apply the middleware to.
        """
        @wraps(func) # Preserve the function metadata.
        def wrapper(event, response=None, context={}):
            """Wrapper function to execute the middleware before the function.

            Args:
                event (any): The event object passed to the function.
                context (any): The context object passed to the function.
                response (Response, optional): The response object passed to the function. Defaults to None.

            Returns:
                any: The result of the function if the middleware does not terminate the request.
            """
            if response is None:
                response = Response()
            event, response, context = middleware(event, response, context)
            if response.terminated:
                return event, response, context
            args = (event, response, context)
            num_args = len(inspect.signature(func).parameters)
            return func(*args[:num_args])
        # Append the middleware's documentation (everything after the '---' separator) to the function's documentation.
        # wrapper.__doc__ = f'{wrapper.__doc__}\n\n{middleware.__doc__}'
        inject_doc = middleware.__doc__.split('---') if middleware.__doc__ else []
        if len(inject_doc) > 1:
            wrapper.__doc__ = f'{wrapper.__doc__}\n\n{inject_doc[1]}'
        return wrapper
    return decorator