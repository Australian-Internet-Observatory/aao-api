from configparser import ConfigParser
from dataclasses import dataclass, field
import json
from opensearchpy import OpenSearch, RequestsHttpConnection
from utils import observations_sub_bucket
from requests_aws4auth import AWS4Auth
import boto3
import botocore
import time

config = ConfigParser()
config.read('config.ini')

OPEN_SEARCH_ENDPOINT = config['OPEN_SEARCH']['ENDPOINT']
SERVICE = 'aoss'
AWS_CONFIG = config['AWS']

session = boto3.Session(
    region_name=AWS_CONFIG['REGION'],
    aws_access_key_id=AWS_CONFIG['ACCESS_KEY_ID'],
    aws_secret_access_key=AWS_CONFIG['SECRET_ACCESS_KEY']
)
credentials = session.get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
                   AWS_CONFIG['REGION'], SERVICE, session_token=credentials.token)

client = OpenSearch(
    hosts=[OPEN_SEARCH_ENDPOINT],
    http_auth=awsauth,
    connection_class=RequestsHttpConnection
)

@dataclass
class AdWithRDO:
    observer_id: str
    timestamp: str
    ad_id: str
    
    rdo_path: str = field(init=False)
    open_search_id: str = field(init=False)
    
    def __post_init__(self):
        self.rdo_path = f"{self.observer_id}/rdo/{self.timestamp}.{self.ad_id}/output.json"
        self.open_search_id = f"{self.observer_id}.{self.ad_id}"
        
    def fetch_rdo(self):
        if not hasattr(self, "rdo_content"):
            self.rdo_content = observations_sub_bucket.read_json_file(self.rdo_path)
            
        fields_to_remove = [
            ['enrichment', 'meta_adlibrary_scrape', 'comparisons'],
            ['enrichment', 'ccl'],
            ['enrichment', 'media'],
            ['media'],
            ['observation', 'whitespace_derived_signature']
        ]

        for field in fields_to_remove:
            try:
                current_level = self.rdo_content
                for key in field[:-1]:
                    current_level = current_level.get(key, {})
                del current_level[field[-1]]
            except KeyError:
                # If the key doesn't exist, we can ignore it
                print(f"Key {field} not found in rdo_content")
                pass
            
        # # Clean the content: enrichment.comparisons, media, observation.whitespace_derived_signature
        # del self.rdo_content["enrichment"]['meta_adlibrary_scrape']["comparisons"]
        # del self.rdo_content["enrichment"]['ccl']
        # del self.rdo_content["enrichment"]['media']
        # del self.rdo_content["media"]
        # del self.rdo_content["observation"]["whitespace_derived_signature"]
        return self.rdo_content

# RDO_INDEX = 'rdo-index'
RDO_INDEX = 'ads-rdo-index'
class RdoOpenSearch:
    def __init__(self):
        self.index = RDO_INDEX
        self.client = client
        
    def search(self, query):
        return self.client.search(index=self.index, body=query, params={
            "timeout": 300 # up to 5 minute / query instead of 10 seconds
        })
    
    def get(self, id):
        return self.client.get(index=self.index, id=id)
    
    def put(self, ad_with_rdo: AdWithRDO, rdo_data):
        return self.client.index(index=self.index, id=ad_with_rdo.open_search_id, body=rdo_data)
    
    def delete(self, id):
        return self.client.delete(index=self.index, id=id)

def get_hit_source_id(hit):
    # Extract the observer id and observation id
    source = hit.get("_source")
    observer = source.get("observer")
    observation = source.get("observation")
    return f"{observer['uuid']}/temp/{observation['uuid']}"

if __name__ == "__main__":
    rdo_search = RdoOpenSearch()
    query = {
        "size": 10000,
        "query": {
            "wildcard": {
                "observation.uuid": "*47e7d7a6*"
            }
        }
    }
    results = rdo_search.search(query)
    hit = results["hits"]["hits"][0]
    print(get_hit_source_id(hit))
    # print(json.dumps(hit['_source']['observation'], indent=4))
    hits = results["hits"]["hits"]
    took = results["took"]
    print(f"Query took {took}ms")
    print(f"Found {len(hits)} hits")
    # print([hit.get("_source").get("observer") for hit in hits])
    # print([get_hit_source_id(hit) for hit in hits])
    # print(rdo_search.search(query))
    # print(rdo_search.search({"query": {"match_all": {}}}))