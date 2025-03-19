import utils.observations_sub_bucket as observations_sub_bucket

methods = {}

class Query:
    def __init__(self, method: str, args: list, context=None):
        self.method = methods[method]
        self.args = args
        self.context = context

    def test(self, value):
        return self.method(self.args, value, self.context)

    def from_dict(dict):
        if isinstance(dict, str):
            return dict
        method = dict["method"]
        args = dict["args"]
        if isinstance(args, list):
            args = [Query.from_dict(arg) for arg in args]
        return Query(method, args)

def register(method_name: str, limit_args=-1):
    """Decorator to register a method to be used in the Query class.

    Args:
        method_name (str): The name of the query method.
        limit_args (int, optional): The number of arguments the method expects. Defaults to -1 (no limit).
    """
    def decorator(func):
        def inner(args, value, context=None):
            if limit_args != -1 and len(args) != limit_args:
                raise ValueError(f"Method {method_name} expects {limit_args} arguments, got {len(args)}")
            return func(args, value, context)
        methods[method_name] = inner
        return inner
    return decorator

# Do not modify AND, OR and NOT methods
@register("AND", limit_args=2)
def AND(args: list[Query], value, context):
    return all(arg.test(value) for arg in args)

@register("OR", limit_args=2)
def OR(args: list[Query], value, context):
    return any(arg.test(value) for arg in args)

@register("NOT", limit_args=1)
def NOT(args: list[Query], value, context):
    return not args[0].test(value)

# Custom methods
def parse_path(ad_path):
    parts = ad_path.split("/")
    return {
        "observer_id": parts[0],
        "timestamp": int(parts[2].split(".")[0]),
        "observation_id": parts[2].split(".")[1]
    }

@register("DATETIME_AFTER", limit_args=1)
def DATETIME_AFTER(args: list[str], ad_path, context):
    """Check if the timestamp of the ad is after the given date.

    Args:
        args (list[str]): A list containing a single string as a timestamp.
        ad_path (str): The path of the ad.

    Returns:
        bool: True if the timestamp is after the given date, False otherwise.
    """
    ad_data = parse_path(ad_path)
    return ad_data["timestamp"] > int(args[0])

@register("DATETIME_BEFORE", limit_args=1)
def DATETIME_BEFORE(args: list[str], ad_path, context):
    ad_data = parse_path(ad_path)
    return ad_data["timestamp"] < int(args[0])

@register("OBSERVER_ID_CONTAINS", limit_args=-1)
def OBSERVER_IN(args: list[str], ad_path, context):
    ad_data = parse_path(ad_path)
    return any(arg in ad_data["observer_id"] for arg in args)

@register("OBSERVATION_ID_CONTAINS", limit_args=-1)
def OBSERVATION_IN(args: list[str], ad_path, context):
    ad_data = parse_path(ad_path)
    return any(arg in ad_data["observation_id"] for arg in args)

class AdQuery:
    def __init__(self):
        # Build the context for the query (e.g., index of the ads)
        self.context = {
            "ads_index": AdQuery.get_ads_index()
        }
        
    def query(self, query_dict: dict):
        query = Query.from_dict(query_dict)
        all_ads = set()
        for ads in AdQuery.get_ads_index().values():
            all_ads.update(ads)
        # Example path: "102c3b74-b6fd-4778-8472-19ec345068a8/temp/1724281969371.c8caeffe-c7d2-4a3b-ae18-030a07743ca6/"
        return [ad_path for ad_path in all_ads if query.test(ad_path)]
        
    @staticmethod
    def get_ads_index():
        ACCEPTED_TYPES = ['ads_passed_mass_download', 'ads_passed_rdo_construction']
        
        index = observations_sub_bucket.read_json_file("ads_stream.json")
        # Convert the index to a dict of sets for faster lookup
        return {key: set(value) for key, value in index.items() if key in ACCEPTED_TYPES}


if __name__ == "__main__":
    query = AdQuery()
    print(query.query({
        "method": "AND",
        "args": [
            {
                "method": "DATETIME_AFTER",
                "args": ["1731012025609"]
            },
            {
                "method": "OBSERVER_ID_CONTAINS",
                "args": ["442eca3f"]
            }
        ]
    }))

# # 
# @register("MATCH", limit_args=1)
# def MATCH(args: list[str], value):
#        return args[0] in value

# @register("EXACT MATCH", limit_args=1)
# def EXACT_MATCH(args: list[str], value):
#        return args[0] == value