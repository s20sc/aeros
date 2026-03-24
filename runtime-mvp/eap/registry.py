import importlib.util
import types

_skill_registry = {}
_eap_registry = {}


def register_skill(name, path, eap_id):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _skill_registry[name] = {
        "module": module,
        "eap_id": eap_id,
    }


def register_eap(eap_id, config, permissions):
    _eap_registry[eap_id] = {
        "config": config,
        "permissions": permissions,
    }


def get_skill(name):
    entry = _skill_registry.get(name)
    if entry:
        return entry
    return None


def get_eap_permissions(eap_id):
    eap = _eap_registry.get(eap_id)
    if not eap:
        return {}
    return eap.get("permissions", {})


def list_skills():
    return list(_skill_registry.keys())


def list_eaps():
    return {eid: e["config"] for eid, e in _eap_registry.items()}
