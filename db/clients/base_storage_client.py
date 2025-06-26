
class BaseStorageClient:
    """Base class for a client to an object storage system that can store and retrieve data.
    
    This class is intended to be subclassed by specific storage client implementations, such as
    Amazon S3, Amazon DynamoDB or any other storage system.
    """
    def __init__(self, **config: dict):
        """Initialize the storage client with configuration parameters.
        
        Args:
            config (dict): Configuration parameters for the storage client.
        """
        self.config = config
        self.connected = False

    def connect(self):
        """Connect to the storage system."""
        raise NotImplementedError("Subclasses should implement this method.")

    def disconnect(self):
        """Disconnect from the storage system."""
        raise NotImplementedError("Subclasses should implement this method.")

    def get(self, keys: dict):
        """Get an object from the storage system by its key. The key is the unique identifier for the object."""
        raise NotImplementedError("Subclasses should implement this method.")
    
    def put(self, value: dict):
        """Put an object into the storage system with the given key and value."""
        raise NotImplementedError("Subclasses should implement this method.")
    
    def delete(self, keys: dict):
        """Delete an object from the storage system by its key."""
        raise NotImplementedError("Subclasses should implement this method.")
    
    def list_ids(self) -> list[dict]:
        """List all object IDs in the storage system."""
        raise NotImplementedError("Subclasses should implement this method.")
    
    def list(self) -> list[dict]:
        """List all objects in the storage system as a list of key-value pairs."""
        raise NotImplementedError("Subclasses should implement this method.")