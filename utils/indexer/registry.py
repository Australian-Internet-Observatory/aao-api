from datetime import datetime

from db.clients.rds_storage_client import RdsStorageClient
from db.repository import Repository
from models.open_search_index import OpenSearchIndex, OpenSearchIndexORM

open_search_index_repository = Repository(
    model=OpenSearchIndex,
    keys=['id'],
    client=RdsStorageClient(
        base_orm=OpenSearchIndexORM,
    )
)

class IndexRegistry:
    def __init__(self):
        self.name = None
    
    def prepare(self, prefix: str = 'index_'):
        # datetime YYYY-MM-DD_HH-MM-SS
        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.name = f"{prefix}{now}"
        print(f"Starting index registry with name: {self.name}")
        open_search_index_repository.create(
            {
                'name': self.name,
                'created_at': int(datetime.now().timestamp()),
                'status': 'created'
            }
        )
        return self
        
    def from_latest(self, status: str = 'ready'):
        latest_index = self.get_latest(status=status)
        if not latest_index:
            raise ValueError("No ready index registry found.")
        self.name = latest_index.name
        print(f"Using latest index registry: {self.name}")
        return self
    
    def get_latest(self, status: str = 'ready') -> OpenSearchIndex:
        """Get the latest index registry."""
        index = open_search_index_repository.get_first({
            'status': status
        }, builder=lambda x: x.order_by(OpenSearchIndexORM.created_at.desc()))
        if not index:
            raise ValueError("No ready index registry found.")
        return index
    
    def start(self):
        if not self.name:
            raise ValueError("Index registry has not been prepared. Call prepare() first.")
        print(f"Index registry {self.name} started.")
        index = open_search_index_repository.get_first({
            'name': self.name
        })
        if not index:
            raise ValueError(f"Index registry {self.name} not found.")
        index.status = 'in_progress'
        open_search_index_repository.update(index)
    
    def fail(self):
        if not self.name:
            raise ValueError("Index registry has not been prepared. Call prepare() first.")
        print(f"Index registry {self.name} failed.")
        index = open_search_index_repository.get_first({
            'name': self.name
        })
        if not index:
            raise ValueError(f"Index registry {self.name} not found.")
        index.status = 'failed'
        open_search_index_repository.update(index)
    
    def complete(self):
        if not self.name:
            raise ValueError("Index registry has not been prepared. Call prepare() first.")
        print(f"Index registry {self.name} completed.")
        index = open_search_index_repository.get_first({
            'name': self.name
        })
        if not index:
            raise ValueError(f"Index registry {self.name} not found.")
        index.status = 'ready'
        open_search_index_repository.update(index)