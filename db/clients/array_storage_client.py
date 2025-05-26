from db.clients.base_storage_client import BaseStorageClient

class ArrayStorageClient(BaseStorageClient):
    """An in-memory storage client that uses a list to store key-value pairs."""
    def __init__(self, **config: dict):
        """Initialize the in-memory storage client with configuration parameters.
        Args:
            config (dict): Configuration parameters for the in-memory storage client.
        """
        super().__init__(**config)
        self.storage = []

    def connect(self):
        """Connect to the in-memory storage."""
        # No actual connection needed for in-memory storage
        return True

    def disconnect(self):
        """Disconnect from the in-memory storage."""
        # No actual disconnection needed for in-memory storage
        return True

    def get(self, key: str):
        """Retrieve an object by its key."""
        for item in self.storage:
            if item['key'] == key:
                return item['value']
        return None

    def put(self, key: str, value):
        """Store an object with the given key and value."""
        self.delete(key)  # Ensure no duplicate keys
        self.storage.append({'key': key, 'value': value})

    def delete(self, key: str):
        """Delete an object by its key."""
        self.storage = [item for item in self.storage if item['key'] != key]

    def list(self):
        """List all objects in the storage."""
        return [item for item in self.storage]