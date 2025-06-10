from functools import wraps
import json
import inspect

class Response:
    def __init__(self):
        self.body = {}
        self.terminated = False
        self.logs = []
        
    def status(self, code: int):
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

def parse_injected_doc(doc):
    """Parse the injected documentation from a middleware function.
    
    Args:
        doc (str): The documentation string to parse.
    
    Returns:
        dict: The parsed documentation.
    """
    injected_parts = doc.split('---') if doc else []
    # Remove the first part of the documentation (the function's original documentation).
    if len(injected_parts) <= 1:
        return {}
    injected_doc = injected_parts[1:]
    # Parse the documentation into a dictionary.
    parsed_doc = {}
    for part in injected_doc:
        lines = part.split('\n')
        key = lines[0].strip()
        # If there is no key, default to 'properties'.
        if not key:
            key = 'properties'
        value = '\n'.join([line for line in lines[1:]])
        parsed_doc[key] = value
    return parsed_doc

def inject_docs(func, middleware):
    """Inject the documentation from a middleware function into the function's documentation.
    
    Args:
        func (function): The function to inject the documentation into.
        middleware (function): The middleware function to extract the documentation from.
    """
    # Extract the injected documentation from the middleware.
    inject_doc = parse_injected_doc(middleware.__doc__)
    middleware_name = middleware.__name__
    # Inject the documentation into the function, based on the specified location.
    if 'summary' in inject_doc:
        # Summary is appended to the first line of the function's documentation.
        first, *rest = func.__doc__.split('\n')
        # Ensure the summary is stripped of any leading/trailing whitespace and newlines.
        stripped_summary = inject_doc["summary"].strip().strip('\n')
        new_first_line = f'{first} [{middleware_name} - {stripped_summary}]\n'
        func.__doc__ = '\n'.join([new_first_line] + rest)
    if 'description' in inject_doc:
        # Description is appended before the "---" separator in the function's documentation.
        parts = func.__doc__.split('---')
        if len(parts) > 1:
            func.__doc__ = f'{parts[0]}\n{inject_doc["description"]}\n\n---{parts[1]}'
        else:
            func.__doc__ = f'{parts[0]}\n{inject_doc["description"]}\n\n'
    if 'properties' in inject_doc:
        # Properties are appended to the end of the function's documentation.
        func.__doc__ = f'{func.__doc__}\n\n{inject_doc["properties"]}'
    
    return func

def use(middleware):
    """Apply a middleware to a function to modify the event and context before the function is executed.
    
    Use `--- {location}` followed by the documentation to append the middleware's documentation to a specific location in the function's documentation.
    
    For example:
    
    ```python
    \"\"\"
    A custom middleware that injects some documentation to the route's documentation.
    --- summary
    This line will be appended to the summary (first line) of the route's documentation.
    --- description
    This line will be appended to the description of the route's documentation.
    
    And so is this line.
    --- properties
    security:
        - bearerAuth: []
    \"\"\"
    ```

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
        return inject_docs(wrapper, middleware)
    return decorator