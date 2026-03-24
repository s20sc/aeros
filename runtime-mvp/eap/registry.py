import importlib.util

# EAP states: installed -> activated -> deactivated -> uninstalled
_skill_registry = {}    # skill_name -> {module, eap_id}
_eap_registry = {}      # eap_id -> {config, permissions, state, path}


def register_eap(eap_id, config, permissions, path):
    _eap_registry[eap_id] = {
        "config": config,
        "permissions": permissions,
        "state": "installed",
        "path": path,
    }


def activate_eap(eap_id):
    eap = _eap_registry.get(eap_id)
    if not eap:
        return False, f"EAP '{eap_id}' not found"
    if eap["state"] == "activated":
        return False, f"EAP '{eap_id}' already activated"
    if eap["state"] == "uninstalled":
        return False, f"EAP '{eap_id}' has been uninstalled"

    # Register skills
    import os
    config = eap["config"]
    skills_dir = os.path.join(eap["path"], "skills")

    for skill_name in config.get("skills", []):
        module_file = skill_name.split(".")[-1] + ".py"
        module_path = os.path.join(skills_dir, module_file)
        if os.path.exists(module_path):
            register_skill(skill_name, module_path, eap_id)

    eap["state"] = "activated"
    return True, None


def deactivate_eap(eap_id):
    eap = _eap_registry.get(eap_id)
    if not eap:
        return False, f"EAP '{eap_id}' not found"
    if eap["state"] != "activated":
        return False, f"EAP '{eap_id}' is not activated (state={eap['state']})"

    # Unregister skills
    config = eap["config"]
    for skill_name in config.get("skills", []):
        _skill_registry.pop(skill_name, None)

    eap["state"] = "deactivated"
    return True, None


def uninstall_eap(eap_id):
    eap = _eap_registry.get(eap_id)
    if not eap:
        return False, f"EAP '{eap_id}' not found"

    # Unregister skills if still active
    if eap["state"] == "activated":
        config = eap["config"]
        for skill_name in config.get("skills", []):
            _skill_registry.pop(skill_name, None)

    eap["state"] = "uninstalled"
    return True, None


def register_skill(name, path, eap_id):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _skill_registry[name] = {
        "module": module,
        "eap_id": eap_id,
    }


def get_skill(name):
    return _skill_registry.get(name)


def get_eap_permissions(eap_id):
    eap = _eap_registry.get(eap_id)
    if not eap:
        return {}
    return eap.get("permissions", {})


def get_eap(eap_id):
    return _eap_registry.get(eap_id)


def list_skills():
    return list(_skill_registry.keys())


def list_eaps():
    return _eap_registry
