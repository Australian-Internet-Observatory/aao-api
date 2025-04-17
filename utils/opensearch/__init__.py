import json
from utils.opensearch.boolean_query_converter import convert_to_opensearch_format
from utils.opensearch.rdo_open_search import RdoOpenSearch, get_hit_source_id

class AdQuery:
    def query(self, query_dict: dict):
        parsed_query = convert_to_opensearch_format(query_dict)
        query = {
            "_source": [
                "observer.uuid",
                "observation.uuid"
            ],
            "size": 10000,
            "sort": [
                # Sort by observation time descending
                {
                    "observation.observed_on_device_at": {
                        "order": "desc"
                    }
                }
            ],
            "query": parsed_query
        }
        # print(json.dumps(opensearch_query, indent=4))
        rdo_search = RdoOpenSearch()
        results = rdo_search.search(query)
        hits = results["hits"]["hits"]
        # print(f"Total hits: {results['hits']['total']['value']}")
        # print(f"First hit: {json.dumps(hits[0], indent=4)}")
        return [get_hit_source_id(hit) for hit in hits]