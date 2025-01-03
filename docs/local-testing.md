# Testing Locally

This project is designed to be run on an AWS Lambda function. We can also test the API locally by importing the `lambda_handler` function in `lambda_function.py` and running it with a sample event.

An event should be a dictionary with the following structure:

```python
event = {
    'path': '/hello',
    'httpMethod': 'GET',
    'headers': {
        'Content-Type': 'application/json'
    },
    'body': None
}
```

Where:

- `path`: The path of the endpoint to be tested, such as `/hello`, or `/users`. This is similar to a URL path, and can contain query parameters.
- `httpMethod`: The HTTP method to be used, such as `GET`, `POST`, `PUT`, `DELETE`, etc.
- `headers`: A dictionary of headers to be sent with the request, such as `Authorization`, `Content-Type`, etc.
- `body`: The request body, if any. This should be a JSON string, like `{"key": "value"}`. If the request does not have a body, do not include this key in the event.

This event can be passed to the `lambda_handler` function to test the API locally. For example:

```python
from lambda_function import lambda_handler

def test_hello():
    event = {
        'path': '/hello',
        'httpMethod': 'GET',
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': None
    }

    response = lambda_handler(event, None)
    print(response)
```

This will print the response from the `/hello` endpoint to the console. You can modify the event to test other endpoints as well.

## Examples

**Login then Access Protected Route**

```python
from lambda_function import lambda_handler

def login():
    data = {
        'username': 'username',
        'password': 'password'
    }
    event = {
        'path': '/auth/login',
        'httpMethod': 'POST',
        'body': json.dumps(data)
    }
    response = lambda_handler(event, None)
    return json.loads(response['body'])

# This is a protected route that requires authentication
def test_create_user():
    token = test_login()['token']
    data = {
        "username": "new_user",
        "enabled": True,
        "password": "password",
        "full_name": "New User",
        "role": "user"
    }
    event = {
        "headers": {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        },
        "httpMethod": "POST",
        "path": "users",
        'body': json.dumps(data)
    }
    response = lambda_handler(event, None)
    print(response)

if __name__ == '__main__':
    test_create_user()
```