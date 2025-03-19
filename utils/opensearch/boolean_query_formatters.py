# Formatters to convert from AAO boolean query to OpenSearch query
formatters = {}

"""query arg format:
{
    "method": str,
    "args": list of str or query
}
"""

# Decorator to register a formatter
def register(method):
    def decorator(func):
        formatters[method] = func
        return func
    return decorator

def get_formatter(method):
    return formatters.get(method, lambda x: {})

@register("DATETIME_AFTER")
def datetime_after(arg):
    return {
        "range": {
            "observation.observed_on_device_at": {
                "gte": int(arg["args"][0][:-3]) # Remove milliseconds
            }
        }
    }

@register("DATETIME_BEFORE")
def datetime_before(arg):
    return {
        "range": {
            "observation.observed_on_device_at": {
                "lte": int(arg["args"][0][:-3]) # Remove milliseconds
            }
        }
    }

@register("OBSERVER_ID_CONTAINS")
def observer_id_contains(arg):
    should_query = [{"wildcard": {"observer.uuid": {"value": f'*{observer_id}*'}}} for observer_id in arg["args"]]
    return {
        "bool": {
            "should": should_query,
            "minimum_should_match": 1
        }
    }

@register("OBSERVATION_ID_CONTAINS")
def observation_id_contains(arg):
    should_query = [{"wildcard": {
            "observation.uuid": {
                "value": f'*{observation_id}*'
            }
        }} for observation_id in arg["args"]]
    return {
        "bool": {
            "should": should_query,
            "minimum_should_match": 1
        }
    }

@register("CATEGORIES_CONTAINS")
def categories_contains(arg):
    should_query = [
        {
            "query_string": {
                "query": f'"{category}"', # Wrap in quotes to search for exact phrase
                "fields": ["enrichment.meta_adlibrary_scrape.candidates.data.categories"],
            }
        } for category in arg["args"]
    ]
    return {
        "bool": {
            "should": should_query,
            "minimum_should_match": 1
        }
    }

@register("PAGE_NAME_CONTAINS")
def page_name_contains(arg):
    should_query = [
        {
            "query_string": {
                "query": f'"{page_name}"', # Wrap in quotes to search for exact phrase
                "fields": ["enrichment.meta_adlibrary_scrape.candidates.data.page_name"],
            }
        } for page_name in arg["args"]
    ]
    # should_query = [
    #     {
    #         "regexp": {
    #             "enrichment.meta_adlibrary_scrape.candidates.data.page_name": f'{page_name}', # Wrap in quotes to search for exact phrase
    #         }
    #     } for page_name in arg["args"]
    # ]
    # should_query = [{"wildcard": {
    #     "enrichment.meta_adlibrary_scrape.candidates.data.page_name":
    #         {
    #             "value": f'{page_name}',
    #             "case_insensitive": True
    #         }
    # }} for page_name in arg["args"]]
    # should_query = [{"match": {
    #     "enrichment.meta_adlibrary_scrape.candidates.data.page_name":
    #         {
    #             "query": f'.*{page_name}.*',
    #         }
    # }} for page_name in arg["args"]]
    return {
        "bool": {
            "should": should_query,
            "minimum_should_match": 1
        }
    }
    
@register("ANYTHING_CONTAINS")
def full_text_contains(arg):
    fields = [
        "*"
    ]
    should_query = [
        {
            "simple_query_string": {
                "query": f'"{text}"', # Wrap in quotes to search for exact phrase
                "fields": fields,
            }
        } for text in arg["args"]]
    return {
        "bool": {
            "should": should_query,
            "minimum_should_match": 1
        }
    }