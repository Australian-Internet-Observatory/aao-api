import json
from utils.opensearch.boolean_query_adapter import convert_to_opensearch_format
from utils.opensearch.rdo_open_search import RdoOpenSearch

def get_hit_source_id(hit):
    # Extract the observer id and observation id
    source = hit.get("_source")
    observer = source.get("observer")
    observation = source.get("observation")
    return f"{observer['uuid']}/temp/{observation['uuid']}"

class AdQuery:
    def query(self, query_dict: dict):
        parsed_query = convert_to_opensearch_format(query_dict)
        query = {
            "size": 10000,
            "query": parsed_query
        }
        # print(json.dumps(opensearch_query, indent=4))
        rdo_search = RdoOpenSearch()
        results = rdo_search.search(query)
        hits = results["hits"]["hits"]
        return [get_hit_source_id(hit) for hit in hits]