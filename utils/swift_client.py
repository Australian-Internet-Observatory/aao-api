"""Swift client helper for OpenStack Swift object storage.

This module provides a small wrapper around `python-swiftclient` that
simplifies uploading/downloading objects and generating temporary URLs.

Example usage:

    # Required environment variables:
    export OS_USERNAME='your-username'
    export OS_PASSWORD='your-password'
    export OS_PROJECT_NAME='your-project'
    export OS_PROJECT_ID='your-project-id'
    # The project ID can be found in the API Access page of the Nectar dashboard.
    # It can be extracted as part of the Object Store Service endpoint URL, e.g.:
    # https://object-store.rc.nectar.org.au/v1/AUTH_{your-project-id}
    # Required for temporary URLs:
    export OS_TEMP_URL_KEY='your-temp-url-key'

    from worker.swift_client import SwiftClient

    client = SwiftClient()
    client.put_object('my-container', 'path/to/myfile.zip', '/tmp/myfile.zip')
    data = client.get_object('my-container', 'path/to/myfile.zip')
    temp_url = client.get_temp_url('my-container', 'path/to/myfile.zip', expires_in=3600)

"""

import logging
import sys
from pathlib import Path
import swiftclient
from swiftclient.utils import generate_temp_url
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

USERNAME = os.getenv("OS_USERNAME", None)
PASSWORD = os.getenv("OS_PASSWORD", None)
PROJECT_NAME = os.getenv("OS_PROJECT_NAME", None)
PROJECT_ID = os.getenv("OS_PROJECT_ID", None)
TEMP_URL_KEY = os.getenv("OS_TEMP_URL_KEY", None)

AUTH_URL = "https://identity.rc.nectar.org.au/v3/"
OBJECT_STORE_URL = "https://object-store.rc.nectar.org.au"
AUTH_VERSION = "3"
OS_OPTIONS = {
    "user_domain_name": "Default",
    "project_domain_id": "default",
    "project_name": PROJECT_NAME
}


class SwiftClient:
    """Simple Swift client wrapper.

    Reads credentials and configuration from environment variables:
      - OS_USERNAME
      - OS_PASSWORD
      - OS_PROJECT_NAME
      - OS_PROJECT_ID (required to generate temporary URLs)
      - OS_TEMP_URL_KEY (optional; required to generate temporary URLs)

    Usage example:

        client = SwiftClient()
        client.put_object('container', 'objname', '/tmp/file.zip')
        data = client.get_object('container', 'objname')
        url = client.get_temp_url('container', 'objname', expires_in=3600)

    Raises:
        ValueError: If required environment variables are missing.
    """

    def __init__(self):
        # Ensure all required environment variables are set
        if not USERNAME:
            raise ValueError("OS_USERNAME environment variable is not set.")
        if not PASSWORD:
            raise ValueError("OS_PASSWORD environment variable is not set.")
        if not PROJECT_NAME:
            raise ValueError(
                "OS_PROJECT_NAME environment variable is not set.")
        self.conn = swiftclient.Connection(
            user=USERNAME,
            key=PASSWORD,
            authurl=AUTH_URL,
            auth_version=AUTH_VERSION,
            os_options=OS_OPTIONS
        )
        # Ensure the temporary URL key is set
        if TEMP_URL_KEY:
            self.conn.post_account(
                {'x-account-meta-temp-url-key': TEMP_URL_KEY})
            logger.info("Temporary URL key set for Swift account.")
        else:
            logger.warning(
                "TEMP_URL_KEY is not set. Temporary URLs will not work.")

    from typing import Optional

    def put_object(self, container_name: str, object_name: str, file_path: str, expiration: Optional[int] = None) -> None:
        """Upload a local file to the specified container.

        This method supports an optional `expiration` parameter which will set
        the `x-delete-after` header on the uploaded object (time in seconds),
        instructing Swift to automatically delete the object after the period.

        Args:
            container_name (str): Swift container name.
            object_name (str): Destination object name in Swift.
            file_path (str): Path to local file to upload.
            expiration (Optional[int]): If provided, number of seconds until the
                object is automatically deleted by Swift.

        Returns:
            None

        Raises:
            FileNotFoundError: If `file_path` does not exist or cannot be opened.
            swiftclient.exceptions.ClientException: If the Swift API returns an error.

        Example:
            client.put_object('my-container', 'path/to/object.zip', '/tmp/file.zip', expiration=3600)
        """
        headers = None
        if expiration is not None:
            headers = {"x-delete-after": str(expiration)}

        with open(file_path, 'rb') as local_file:
            self.conn.put_object(
                container_name,
                object_name,
                contents=local_file,
                headers=headers
            )
            logger.info(
                f"Uploaded {object_name} to container {container_name}")

    def get_object(self, container_name: str, object_name: str) -> bytes:
        """Retrieve an object from Swift.

        Args:
            container_name (str): Swift container name.
            object_name (str): The object name to retrieve.

        Returns:
            bytes: The raw content of the object.

        Raises:
            swiftclient.exceptions.ClientException: If the object cannot be retrieved.
        """
        obj_tuple = self.conn.get_object(container_name, object_name)
        logger.info(f"Retrieved {object_name} from container {container_name}")
        return obj_tuple[1]

    def get_temp_url(self, container_name: str, object_name: str, expires_in: int = 3600) -> str:
        """Generate a temporary public URL for an object.

        The temporary URL feature requires a temp URL key to be set on the
        account (`OS_TEMP_URL_KEY`) and a project ID to build the object path
        (`OS_PROJECT_ID`). The project ID is used to construct the AUTH path
        portion of the temporary URL.

        Args:
            container_name (str): Swift container name.
            object_name (str): Object name to create the temporary URL for.
            expires_in (int): Expiration time in seconds (default: 3600).

        Returns:
            str: Full URL to access the object.

        Raises:
            RuntimeError: If `OS_TEMP_URL_KEY` is not set.
            ValueError: If `OS_PROJECT_ID` is not set (required to build the URL).
        """
        if not TEMP_URL_KEY:
            raise RuntimeError(
                "TEMP_URL_KEY is not set. Cannot generate temporary URL. Use environment variable OS_TEMP_URL_KEY.")
        if not PROJECT_ID:
            raise ValueError(
                "OS_PROJECT_ID is not set. Set OS_PROJECT_ID to your project ID (see Nectar dashboard or object-store endpoint URL).")

        temp_url = generate_temp_url(
            path=f"/v1/AUTH_{PROJECT_ID}/{container_name}/{object_name}",
            seconds=expires_in,
            key=TEMP_URL_KEY,
            method='GET',
        )
        logger.info(
            f"Successfully generated temporary URL for {object_name} in container {container_name}: {OBJECT_STORE_URL}{temp_url}")
        return f"{OBJECT_STORE_URL}{temp_url}"
