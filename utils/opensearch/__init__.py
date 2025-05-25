import json
from utils.opensearch.boolean_query_converter import convert_to_opensearch_format
from utils.opensearch.rdo_open_search import RdoOpenSearch, get_hit_source_id

class AdQuery:
    def query(self, query_dict: dict):
        # Limit the page size to avoid exceeding OpenSearch timeout
        PAGE_SIZE = 1000
        MAX_RESULTS = 1_000_000
        max_retries = (MAX_RESULTS // PAGE_SIZE)
        
        parsed_query = convert_to_opensearch_format(query_dict)
        query = {
            "_source": [
                "observer.uuid",
                "observation.uuid"
            ],
            "size": PAGE_SIZE,
            "track_total_hits": True,
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
        print("Parsed OpenSearch query:")
        print(json.dumps(query, indent=4))
        rdo_search = RdoOpenSearch()
        results = rdo_search.search(query)
        hits = results["hits"]["hits"]
        print(f"Initial query took {results['took']}ms")
        if not hits or len(hits) == 0:
            return []
        
        last_hit = hits[-1]

        for i in range(max_retries):
            next_query = {
                **query,
                "search_after": last_hit["sort"],
            }
            results = rdo_search.search(next_query)
            print(f"Query took {results['took']}ms")
            
            # If no more hits, break
            if not results["hits"]["hits"]:
                break
            hits += results["hits"]["hits"]
            last_hit = hits[-1]
        
        print(f"Total hits: {len(hits)}")
        # print(f"First hit: {json.dumps(hits[0], indent=4)}")
        hit_ids = [get_hit_source_id(hit) for hit in hits]
        print("Removing duplicates...")
        unique_hit_ids = list(set(hit_ids))
        print(f"Unique hits: {len(unique_hit_ids)}")
        return unique_hit_ids