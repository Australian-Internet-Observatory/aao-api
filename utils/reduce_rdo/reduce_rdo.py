import map_json
from mappings.v1 import mapping as v1_mapping
from mappings.v2 import mapping as v2_mapping

mappings_by_version = {
    1: v1_mapping,
    2: v2_mapping,
}

def reduce_rdo(data, version=2, verbose=False):
    """Reduce the JSON data based on the provided mapping."""
    if version not in mappings_by_version:
        raise ValueError(f"Unsupported version: {version}. Supported versions are: {list(mappings_by_version.keys())}")
    mapping = mappings_by_version[version]
    return map_json.map_json(data, mapping, verbose)