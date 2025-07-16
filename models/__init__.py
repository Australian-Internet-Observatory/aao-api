import importlib
import glob

# List all files in the current directory
models = glob.glob("models/*.py")
modules = []

for file in models:
    # Extract the module name from the file path
    module_name = file[:-3].replace("/", ".")
    if module_name != "models.__init__":
        # Import the module dynamically
        module = importlib.import_module(module_name)
        modules.append(module)
        
# Emulate from module import * behaviour
for module in modules:
    names = [name for name in module.__dict__ if not name.startswith('_')]
    globals().update({name: getattr(module, name) for name in names})