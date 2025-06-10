from . import map_json
from .mappings.v1 import mapping as v1_mapping
from .mappings.v2 import mapping as v2_mapping

mappings_by_version = {
    1: v1_mapping,
    2: v2_mapping,
}

class RdoReducer:
    # def __init__(self, version=2, mapping=None):
    #     # If a specific mapping is provided, use it directly
    #     if mapping is not None:
    #         self.mapping = mapping
    #         return
        
    #     # Otherwise, use the mapping based on the version
    #     if version not in mappings_by_version:
    #         raise ValueError(f"Unsupported version: {version}. Supported versions are: {list(mappings_by_version.keys())}")
    #     self.mapping = mappings_by_version[version]
    
    def set_mapping(self, mapping: dict):
        """Set the mapping to be used for reduction."""
        self.mapping = mapping
        return self
    
    def set_version(self, version: int):
        """Set the mapping based on the version."""
        if version not in mappings_by_version:
            raise ValueError(f"Unsupported version: {version}. Supported versions are: {list(mappings_by_version.keys())}")
        self.mapping = mappings_by_version[version]
        return self

    def reduce(self, data, verbose=False):
        """Reduce the JSON data based on the provided mapping."""
        return map_json.map_json(data, self.mapping, verbose)

    def __call__(self, data, verbose=False):
        """Allow the object to be called like a function."""
        return self.reduce(data, verbose)
        

# def reduce_rdo(data, version=2, verbose=False):
#     """Reduce the JSON data based on the provided mapping."""
#     if version not in mappings_by_version:
#         raise ValueError(f"Unsupported version: {version}. Supported versions are: {list(mappings_by_version.keys())}")
#     mapping = mappings_by_version[version]
#     return map_json.map_json(data, mapping, verbose)