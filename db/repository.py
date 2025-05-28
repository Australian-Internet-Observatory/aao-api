from pydantic import BaseModel
from db.clients.base_storage_client import BaseStorageClient
from uuid import uuid4

class Repository():
    def __init__(self, model: BaseModel = BaseModel, client: BaseStorageClient = BaseStorageClient):
        self._client = client
        self._model = model
        client.connect()

    def create(self, item: dict | BaseModel) -> dict:
        """Add a new item to the storage, if it doesn't exist"""
        print("[Repository] create", item)
        existing_ids = self._client.list_ids()
        if isinstance(item, BaseModel):
            item = item.model_dump()
        
        # If does not have an id, generate one
        if not item.get('id'):
            item['id'] = str(uuid4())
        if str(item.get('id')) in existing_ids:
            raise ValueError(f"Item with ID {item.get('id')} already exists.")
        self._client.put(str(item.get('id')), item)
        return item

    def update(self, item: dict | BaseModel) -> None:
        """Update an existing item in the storage."""
        # If item is a dict, convert it to the model
        if isinstance(item, dict):
            item = self._model.model_validate(item)
        print("[Repository] update", item)
        if str(item.id) not in self._client.list_ids():
            raise ValueError(f"Item with ID {item.id} does not exist.")
        self._client.put(str(item.id), item.model_dump())

    def create_or_update(self, item: dict | BaseModel) -> None:
        """Create or update an item in the storage."""
        # If item is a base model, convert it to a dict
        if isinstance(item, BaseModel):
            item = item.model_dump()
        print("[Repository] create_or_update", item)
        # If not have id, or not in the list, create it
        if not item.get('id') or str(item.get('id')) not in self._client.list_ids():
            print("[Repository] create_or_update - create")
            return self.create(item)
        # If has an id, use the update method
        else:
            print("[Repository] create_or_update - update")
            return self.update(self._model.model_validate(item))

    def list(self) -> list[BaseModel]:
        """Retrieve all items from the storage."""
        items = self._client.list()
        return [self._model.model_validate(item['value']) for item in items]

    def get(self, item_id: int | str, default = None) -> BaseModel | None:
        """Retrieve an item by its ID."""
        data = self._client.get(str(item_id))
        return self._model.model_validate(data) if data else default

    def delete(self, item: BaseModel | dict | str) -> None:
        """Remove an item from the storage."""
        if isinstance(item, BaseModel):
            item_id = str(item.id)
        elif isinstance(item, dict):
            item_id = str(item.get('id'))
        elif isinstance(item, str):
            item_id = str(item)
        self._client.delete(item_id)