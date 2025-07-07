from typing import List
from pydantic import BaseModel
from db.clients.base_storage_client import BaseStorageClient
from uuid import uuid4

def list_contains_dict(lst: list[dict], item: dict) -> bool:
    """Check if a list of dictionaries contains a dictionary with the same keys and values."""
    for d in lst:
        if all(d.get(k) == item.get(k) for k in item):
            return True
    return False

class Repository():
    def __init__(self, 
                 model: BaseModel = BaseModel, 
                 client: BaseStorageClient = BaseStorageClient, 
                 keys: list[str] = ['id'],
                 auto_generate_key: bool = True,
                 verbose: bool = False,
                 auto_connect: bool = False
                ):
        """Initialize the repository with a model and a storage client.
        
        Args:
            model (BaseModel): The Pydantic model to use for validation.
            client (BaseStorageClient): The storage client to use for data operations.
            keys (list[str]): The list of primary keys to identify items in the storage.
            auto_generate_key (bool): Whether to automatically generate keys if they are not provided.
            verbose (bool): Whether to print verbose output for debugging.
        """
        self._client = client
        self._model = model
        self._keys = keys
        self._auto_generate_key = auto_generate_key
        self._verbose = verbose
        if auto_connect:
            self.connect()

    def connect(self) -> None:
        """Connect to the storage client."""
        if self._verbose: print("[Repository] connect")
        self._client.connect()
    
    def disconnect(self) -> None:
        """Disconnect from the storage client."""
        if self._verbose: print("[Repository] disconnect")
        self._client.disconnect()

    def create(self, item: dict | BaseModel) -> dict:
        """Add a new item to the storage, if it doesn't exist"""
        if self._verbose: print("[Repository] create", item)
        existing_keys = self._client.list_ids()
        if isinstance(item, BaseModel):
            item = item.model_dump()
        
        # If does not have an id, generate one
        keys = { key: item.get(key, None) for key in self._keys }
        if list_contains_dict(existing_keys, keys):
            raise ValueError(f"Item with keys {keys} already exists.")
        
        # If auto_generate_key is True, generate them
        for key in self._keys:
            if self._auto_generate_key and not item.get(key):
                item[key] = str(uuid4())
            elif key not in item:
                raise ValueError(f"Item must have a '{key}' key.")
        
        self._client.put(item)
        return item

    def update(self, item: dict | BaseModel) -> None:
        """Update an existing item in the storage."""
        # If item is a dict, convert it to the model
        if isinstance(item, dict):
            item = self._model.model_validate(item)
        if self._verbose: print("[Repository] update", item)
        
        keys = { key: item.model_dump()[key] for key in self._keys }
        existing_keys = self._client.list_ids()
        if not list_contains_dict(existing_keys, keys):
            raise ValueError(f"Item with keys {keys} does not exist.")
        
        self._client.put(item.model_dump())

    def create_or_update(self, item: dict | BaseModel) -> None:
        """Create or update an item in the storage."""
        # If item is a base model, convert it to a dict
        if isinstance(item, BaseModel):
            item = item.model_dump()
        if self._verbose: print("[Repository] create_or_update", item)
        keys = { key: item[key] for key in self._keys }
        existing_keys = self._client.list_ids()
        if not list_contains_dict(existing_keys, keys):
            if self._verbose: print("[Repository] create_or_update - create")
            return self.create(item)
        else:
            if self._verbose: print("[Repository] create_or_update - update")
            return self.update(self._model.model_validate(item))

    def list(self) -> list[BaseModel]:
        """Retrieve all items from the storage."""
        items = self._client.list()
        return [self._model.model_validate(item['value']) for item in items]

    def get(self, keys: dict, default = None) -> BaseModel | List | None:
        """Retrieve one or more items from the storage by one or more keys."""
        data = self._client.get(keys)
        if data is None:
            return default
        return [self._model.model_validate(item) for item in data]

    def get_first(self, keys: dict, default = None, **kwargs) -> BaseModel | None:
        """Retrieve the first item from the storage by one or more keys."""
        data = self._client.get(keys, **kwargs)
        if not data or len(data) == 0:
            return default
        return self._model.model_validate(data[0])

    def delete(self, item: BaseModel | dict) -> None:
        """Delete an item from the storage."""
        if isinstance(item, BaseModel):
            dump = item.model_dump()
            item_keys = { key: dump[key] for key in self._keys if key in dump }
        elif isinstance(item, dict):
            item_keys = item
        elif isinstance(item, frozenset):
            item_keys = str(item)
        self._client.delete(item_keys)
        
    def create_session(self) -> 'RepositorySession':
        """Create a session for the repository."""
        return RepositorySession(self)
        
class RepositorySession():
    def __init__(self, repository: 'Repository'):
        """Initialize the repository session."""
        self._repository = repository

    def __enter__(self):
        """Enter the repository session."""
        self._repository.connect()
        return self._repository

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the repository session."""
        self._repository.disconnect()
        
    # Session methods are the same as the repository methods
    def create(self, item: dict | BaseModel) -> dict:
        """Add a new item to the storage, if it doesn't exist."""
        return self._repository.create(item)
    
    def update(self, item: dict | BaseModel) -> None:
        """Update an existing item in the storage."""
        return self._repository.update(item)
    
    def create_or_update(self, item: dict | BaseModel) -> None:
        """Create or update an item in the storage."""
        return self._repository.create_or_update(item)
    
    def list(self) -> list[BaseModel]:
        """Retrieve all items from the storage."""
        return self._repository.list()
    
    def get(self, keys: dict, default = None) -> BaseModel | List | None:
        """Retrieve one or more items from the storage by one or more keys."""
        return self._repository.get(keys, default)
    
    def get_first(self, keys: dict, default = None, **kwargs) -> BaseModel | None:
        """Retrieve the first item from the storage by one or more keys."""
        return self._repository.get_first(keys, default, **kwargs)
    
    def delete(self, item: BaseModel | dict) -> None:
        """Delete an item from the storage."""
        return self._repository.delete(item)