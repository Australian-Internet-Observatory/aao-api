import json
from utils.opensearch.boolean_query_converter import convert_to_opensearch_format
from utils.opensearch.rdo_open_search import LATEST_READY_INDEX, RdoOpenSearch, get_hit_source_id

def create_query(query_dict: dict, page_size: int = 1000):
    """
    Create a query dictionary for OpenSearch.
    
    Args:
        query_dict (dict): The query dictionary to convert. Must include
        a 'method' and 'args' keys.
        
    Returns:
        dict: The OpenSearch formatted query.
    """
    parsed_query = convert_to_opensearch_format(query_dict)
    query = {
        "_source": [
            "observer.uuid",
            "observation.uuid"
        ],
        "size": page_size,
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
    return query

def execute_open_search_query(
                                query: dict, 
                                index: str | None = LATEST_READY_INDEX
                            ):
    """
    Execute a query against the OpenSearch database.
    
    Args:
        query (dict): The OpenSearch query to execute.
        
    Returns:
        dict: The results of the query.
    """
    print("Executing OpenSearch query:")
    print(json.dumps(query, indent=4))
    rdo_search = RdoOpenSearch(index=index)
    results = rdo_search.search(query)
    print(f"Query took {results['took']}ms")
    hits = results["hits"]["hits"]
    if not hits:
        print("No hits found.")
        return [], None, 0
    total_results = results["hits"]["total"]["value"]
    print(f"Total results: {total_results}")
    
    hit_ids = [get_hit_source_id(hit) for hit in hits]
    print(f"Hits: {len(hit_ids)}")
    # print(f"Last hit", hits[-1])
    last_sort_key = hits[-1].get("sort", [])[0] if hits else None
    
    is_last_page = len(hit_ids) < query["size"]
    if is_last_page:
        return hit_ids, None, total_results
    
    return hit_ids, str(last_sort_key), total_results

class AdQuery:
    def create_session(self):
        """
        Create a session for querying the OpenSearch database.
        
        Returns:
            session_id (str): A session ID for the query.
        """
        
        # Use OpenSearch Point-In-Time (PIT) to manage query sessions
        print("Creating a new query session from", LATEST_READY_INDEX)
        rdo_search = RdoOpenSearch(index=LATEST_READY_INDEX)
        pit_id = rdo_search.create_pit()
        return pit_id
    
    def query_paginated(self, 
                        query_dict: dict, 
                        session_id: str, 
                        page_size: int = 1000,
                        search_after: list = None
                        ):
        query = {
            **create_query(query_dict, page_size=page_size),
            "pit": {
                "id": session_id,
                "keep_alive": "5m"  # Keep the PIT alive for another 5 minutes
            },
        }
        if search_after:
            query["search_after"] = [search_after]
        ad_ids, last_sort_key, total_results = execute_open_search_query(query, index=None)
        if not ad_ids:
            print("No hits found.")
            return [], None, total_results
        print(f"Paginated query returned {len(ad_ids)} hits.")
        print(f"Last sort key: {last_sort_key}")
        return ad_ids, last_sort_key, total_results
    
    def query_all(self, query_dict: dict):
        # Limit the page size to avoid exceeding OpenSearch timeout
        PAGE_SIZE = 1000
        MAX_RESULTS = 1_000_000
        
        query = create_query(query_dict, page_size=PAGE_SIZE)
        ad_ids, last_sort_key, total_results = execute_open_search_query(query)
        max_retries = (min(MAX_RESULTS, total_results) // PAGE_SIZE)
        print(f"Initial hits: {len(ad_ids)}, last sort key: {last_sort_key}")

        for i in range(max_retries):
            next_query = {
                **query,
            }
            if last_sort_key:
                next_query["search_after"] = [last_sort_key]
            next_ad_ids, last_sort_key, _ = execute_open_search_query(next_query)
            if not next_ad_ids or len(next_ad_ids) == 0:
                print(f"No more hits found after {i + 1} iterations.")
                break
            ad_ids += next_ad_ids
        
        print(f"Total hits: {len(ad_ids)}")
        print("Removing duplicates...")
        unique_ad_ids = list(set(ad_ids))
        print(f"Unique hits: {len(unique_ad_ids)}")
        return unique_ad_ids