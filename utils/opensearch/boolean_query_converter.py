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
        opensearch_query["bool"]["filter"] = [convert_arg(arg) for arg in query["args"]]
    elif query["method"] == "OR":
        opensearch_query["bool"]["should"] = [convert_arg(arg) for arg in query["args"]]
    elif query["method"] == "NOT":
        opensearch_query["bool"]["must_not"] = [convert_arg(arg) for arg in query["args"]]
    else:
        opensearch_query = convert_arg(query)

    return opensearch_query