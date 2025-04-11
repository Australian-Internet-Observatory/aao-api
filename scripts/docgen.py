from routes import get_path_param_keys, parse_path_parameters, routes
import yaml
import lambda_function
from scripts.parse_schemas import create_openapi_schema # To capture routes not in 'routes' folder

api_description = """
openapi: 3.0.3
info:
  title: Australian Ad Observatory API
  description: |-
    This is the documentation for the API used in the Australian Ad Observatory (AAO) project.
    
    The API is used to access the data collected by the AAO, with a focus on the data collected from the Australian Mobile Ad Toolkit on Android devices. The toolkit collects data on the ads displayed on the device, including the ad content, the app displaying the ad and more. To use this API, you will need to authenticate using a JWT token through an account granted by the AAO team.
  termsOfService: http://swagger.io/terms/
  contact:
    email: d.k.tran@uq.edu.au
  license:
    name: MIT
    url: https://opensource.org/license/mit
  version: 1.0.0
externalDocs:
  description: Find out more about the Australian Ad Observatory
  url: https://www.admscentre.org.au/adobservatory/
servers:
  - url: https://f06kj1k332.execute-api.ap-southeast-2.amazonaws.com/dev/
"""

components = """
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
"""

default_body = """
responses:
    200:
        description: OK
    400:
        description: Bad Request
"""

def indent(text, level=1, spaces=2, newline=True):
    # return " " * spaces * level + text + ("\n" if newline else "")
    lines = text.split("\n")
    lines = [f"{' ' * spaces * level}{line}" for line in lines]
    return "\n".join(lines) + ("\n" if newline else "")

def format_docstring(docstring):
    """Format the docstring to be YAML-compliant (consistent spacing, etc.)"""
    yaml_doc = yaml.load(docstring, Loader=yaml.FullLoader)
    return yaml.dump(yaml_doc, sort_keys=False)

def has_property(yaml_string, property_name):
    yaml_obj = yaml.load(yaml_string, Loader=yaml.FullLoader)
    return property_name in yaml_obj

def has_path_parameters(path):
    return "{" in path and "}" in path

def generate_routes_docs():
    """
    Generate documentation for all routes by parsing the docstrings of each route and returning a Swagger-compliant YAML string.
    """
    paths = routes.keys()
    docs = "paths:\n"
    for path in paths:
        formatted_path = path if path.startswith("/") else f"/{path}"
        docs += indent(f"{formatted_path}:", 1)
        methods = routes[path].keys()
        for method in methods:
            docs += indent(f'{method.lower()}:', 2)
            
            current_method_doc = ""
            raw_doc = routes[path][method].__doc__
            if raw_doc is None:
                raw_doc = ""
            parts = raw_doc.split("---")
            head = parts[0]
            head = head.strip().split("\n")
            summary = head[0]
            if len(summary) > 0:
                current_method_doc = indent("summary: " + summary, 3)
            
            if len(head) > 1:
                description = "|-\n" + indent("\n".join([line.strip() for line in head[1:]]).strip(), 1, newline=False)
                current_method_doc += indent(format_docstring("description: " + description), 3)
            
            body = parts[1] if len(parts) > 1 else default_body
            body = format_docstring(body)
            
            if has_path_parameters(path):
                params_obj = {
                    "parameters": []
                }
                params = get_path_param_keys(path)
                for param in params:
                    params_obj["parameters"].append({
                        "name": param,
                        "in": "path",
                        "required": True,
                        "schema": {
                            "type": "string"
                        }
                    })
                param_doc = yaml.dump(params_obj, sort_keys=False)
                body = param_doc + body
                body = format_docstring(body)
            
            current_method_doc += indent(body.strip(), 3)
            
            docs += current_method_doc
            print(path, method)
    return docs

def main():
    routes_docs = generate_routes_docs()
    api_docs = format_docstring(api_description)
    print("Creating schemas...")
    schemas = create_openapi_schema(base_indent=2)
    print("Schemas:\n", schemas)
    # print(api_docs + routes_docs)
    # Save the documentation to a file
    with open("swagger.yaml", "w") as f:
        f.write(api_docs + routes_docs + components + schemas)

if __name__ == "__main__":
    main()