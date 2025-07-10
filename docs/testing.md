# Writing Tests

## Integration Tests

This project is designed to be run on an AWS Lambda function. We can test it locally by placing the test code in the `apitests` directory and running it with the `pytest` command. The test files should be named with the prefix `test_` to be recognised by pytest.

A `base.py` file is provided in the `apitests` directory to set up the test environment. This file exports an `execute_endpoint` function that can be used to call the API endpoints, and has the following signature:

```python
def execute_endpoint(endpoint:str, 
                     method: Literal['GET', 'POST', 'DELETE', 'PUT', 'PATCH']='GET', 
                     body:dict | None = None, 
                     headers:dict | None = None, 
                     auth = False
                    ):
    """
    Execute a local API endpoint with the given method and body.
    
    :param endpoint: The API endpoint to call.
    :param method: The HTTP method to use (default is 'GET').
    :param body: The request body (default is None).
    :param headers: Additional headers to include in the request (default is None).
    :return: The response from the API call.
    """
```

You can use this function to call any API endpoint in your tests. For example, to test the `/hello` endpoint, you can create a test file `test_hello.py` in the `apitests` directory with the following content:

```python
from base import execute_endpoint

def test_hello():
    response = execute_endpoint('/hello')
    assert response.status_code == 200
    assert response.json() == {'message': 'Hello, world!'}
```