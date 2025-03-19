import json
from utils.opensearch.boolean_query_formatters import get_formatter

def convert_to_opensearch_format(query):
    def convert_arg(arg):
        if arg["method"] in ["AND", "OR", "NOT"]:
            return convert_to_opensearch_format(arg)
        formatter = get_formatter(arg["method"])
        return formatter(arg)

    opensearch_query = {
        "bool": {}
    }

    if query["method"] == "AND":
        opensearch_query["bool"]["must"] = [convert_arg(arg) for arg in query["args"]]
    elif query["method"] == "OR":
        opensearch_query["bool"]["should"] = [convert_arg(arg) for arg in query["args"]]
    elif query["method"] == "NOT":
        opensearch_query["bool"]["must_not"] = [convert_arg(arg) for arg in query["args"]]
    else:
        opensearch_query = convert_arg(query)

    # print(json.dumps(opensearch_query, indent=4))

    return opensearch_query

# Example usage
# raw_query = {
#     "method": "AND",
#     "args": [
#         {
#             "method": "AND",
#             "args": [
#                 {
#                     "method": "DATETIME_AFTER",
#                     "args": ["1726408800000"]
#                 },
#                 {
#                     "method": "DATETIME_BEFORE",
#                     "args": ["1728223140000"]
#                 }
#             ]
#         },
#         {
#             "method": "OBSERVER_ID_CONTAINS",
#             "args": ["3677b622", "5ea80108", "f7440767", "7f7277ba", "471c82ad"]
#         }
#     ]
# }

# raw_query = {
#     "method": "PAGE_NAME_CONTAINS",
#     "args": ["Offenders Exposed"]
# }

# if __name__ == "__main__":
#     parsed_query = convert_to_opensearch_format(raw_query)
#     print(json.dumps(parsed_query, indent=4))
#     query = {
#         "size": 10000,
#         "query": parsed_query
#     }
#     # print(json.dumps(opensearch_query, indent=4))
#     rdo_search = RdoOpenSearch()
#     results = rdo_search.search(query)
#     hits = results["hits"]["hits"]
#     took = results["took"]
#     print(f"Query took {took}ms")
#     print(f"Found {len(hits)} hits")