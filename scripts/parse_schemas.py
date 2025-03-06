import json
import yaml
from pydantic.json_schema import models_json_schema
import inspect
import models

def create_openapi_schema_for_models(models):
    _, schemas = models_json_schema(
        [(model, "validation") for model in models],
        ref_template="#/components/schemas/{model}",
    )
    openapi_schema = {
        "schemas": schemas.get('$defs'),
    }
    yaml_schema = yaml.dump(openapi_schema, sort_keys=False, indent=2)
    return yaml_schema

def create_openapi_schema(base_indent=0):
    # Get all the models defined in the models module, and is not a BaseModel
    models_members = inspect.getmembers(models, inspect.isclass)
    non_base_models = [model for name, model in models_members if not name == "BaseModel"]
    yaml_schema = create_openapi_schema_for_models(non_base_models)
    # Indent the yaml schema
    indented_schema = "\n".join([" " * base_indent + line for line in yaml_schema.split("\n")])
    return indented_schema

if __name__ == '__main__':
    print(create_openapi_schema())