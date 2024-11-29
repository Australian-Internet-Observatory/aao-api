from middlewares.authenticate import authenticate
from routes import route
import s3
from utils import use

@route('observers', 'GET')
@use(authenticate)
# Event not used directly, but needed to authenticate
def list_observers(event):
    """List all observers.

    Retrieve a list of all observers from the S3 bucket.
    ---
    tags:
        - observers
    responses:
        200:
            description: A successful response
            content:
                application/json:
                    schema:
                        type: array
                        items:
                            type: string
        400:
            description: A failed response
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                                example: False
                            comment:
                                type: string
    """
    dirs = s3.list_dir()
    return [path for path in dirs if path.endswith("/")]