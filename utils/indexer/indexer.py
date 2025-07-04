"""Indexer module for handling ad indexing for querying."""

from typing_extensions import Literal
from db.clients.rds_storage_client import RdsStorageClient
from db.repository import Repository
from models.observation import Observation, ObservationORM
from utils.opensearch.rdo_open_search import AdWithRDO, RdoOpenSearch

observations_repository = Repository(
    model=Observation,
    keys=['observation_id'],
    client=RdsStorageClient(
        base_orm=ObservationORM,
    )
)

class Indexer:
    def __init__(self, 
                 stage: Literal['prod', 'test', 'staging']='prod',
                 index_name: str | None = None, 
                 skip_on_error=True):
        self.stage = stage
        self.skip_on_error = skip_on_error
        self.index_name = index_name
        
    def put_index_rds(self, observer_id: str, timestamp: str, ad_id: str):
        """Add an observation to an RDS table."""
        observation = Observation(
            observer_id=observer_id,
            observation_id=ad_id,
            timestamp=int(timestamp)
        )
        try:
            observations_repository.create(observation)
        except Exception as e:
            print(f"Error indexing ad {ad_id}: {str(e)}")
            if not self.skip_on_error:
                raise e
        
    def put_index_open_search(self, observer_id: str, timestamp: str, ad_id: str):
        """Put an ad into OpenSearch index."""
        if not self.index_name:
            raise ValueError("No index name provided. Please set index_name before indexing.")
        index_name = self.index_name
        
        try:
            open_search = RdoOpenSearch(index=index_name)
            open_search.put(ad_with_rdo=AdWithRDO(
                observer_id=observer_id,
                timestamp=timestamp,
                ad_id=ad_id
            ))
        except Exception as e:
            print(f"Error indexing ad {ad_id}: {str(e)}")
            if not self.skip_on_error:
                raise e