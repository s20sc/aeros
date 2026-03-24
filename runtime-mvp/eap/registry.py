import importlib.util

_registry = {}


def register_skill(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _registry[name] = module


def get_skill(name):
    return _registry.get(name)


def list_skills():
    return list(_registry.keys())
