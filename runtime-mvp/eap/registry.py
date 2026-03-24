import importlib.util
import types

_registry = {}
_eaps = {}


def register_skill(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _registry[name] = module


def register_eap(eap_id, config):
    _eaps[eap_id] = config


def get_skill(name):
    return _registry.get(name)


def make_stub_skill(name):
    """Create a stub module for unregistered skills (lets policy check run)."""
    module = types.ModuleType(name)
    def run():
        print(f"[Skill]    Executing: {name}")
    module.run = run
    return module


def list_skills():
    return list(_registry.keys())


def list_eaps():
    return _eaps
