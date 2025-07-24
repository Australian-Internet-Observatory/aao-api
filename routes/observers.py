from middlewares.authenticate import authenticate
from middlewares.authorise import Role, authorise
from routes import route
import utils.observations_sub_bucket as observations_sub_bucket
from utils import Response, use

@route('observers', 'GET')
@use(authenticate)
@use(authorise(Role.USER, Role.ADMIN))
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
    dirs = observations_sub_bucket.list_dir()
    return [path for path in dirs if path.endswith("/")]

@route('observers/{observer_id}/csr', 'GET')
@use(authenticate)
@use(authorise(Role.USER, Role.ADMIN))
def get_observer_csr(event, response: Response):
    """Get the CSR for an observer.
    
    Retrieve the presigned URL for the latest CSR of an observer.
    ---
    tags:
        - observers
    responses:
        200:
            description: A successful response with the presigned URL
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            success:
                                type: boolean
                                example: True
                            presign_url:
                                type: string
        404:
            description: No CSR found for the observer
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
                                example: "No CSR found for this observer."
    """
    observer_id = event['pathParameters']['observer_id']
    observer = observations_sub_bucket.Observer(observer_id)
    presign_url = observer.get_latest_csr_presign_url()
    if not presign_url:
        return response.status(404).json({
            "success": False,
            "comment": "No CSR found for this observer."
        })
    return {
        "success": True,
        "presign_url": observer.get_latest_csr_presign_url()
    }