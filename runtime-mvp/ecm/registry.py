import importlib.util

# ECM states: installed -> activated -> deactivated -> uninstalled
_skill_registry = {}    # skill_name -> {module, ecm_id}
_ecm_registry = {}      # ecm_id -> {config, permissions, state, path}


def register_ecm(ecm_id, config, permissions, path):
    _ecm_registry[ecm_id] = {
        "config": config,
        "permissions": permissions,
        "state": "installed",
        "path": path,
    }


def activate_ecm(ecm_id):
    ecm = _ecm_registry.get(ecm_id)
    if not ecm:
        return False, f"ECM '{ecm_id}' not found"
    if ecm["state"] == "activated":
        return False, f"ECM '{ecm_id}' already activated"
    if ecm["state"] == "uninstalled":
        return False, f"ECM '{ecm_id}' has been uninstalled"

    # Register skills
    import os
    config = ecm["config"]
    skills_dir = os.path.join(ecm["path"], "skills")

    for skill_name in config.get("skills", []):
        module_file = skill_name.split(".")[-1] + ".py"
        module_path = os.path.join(skills_dir, module_file)
        if os.path.exists(module_path):
            register_skill(skill_name, module_path, ecm_id)

    ecm["state"] = "activated"
    return True, None


def deactivate_ecm(ecm_id):
    ecm = _ecm_registry.get(ecm_id)
    if not ecm:
        return False, f"ECM '{ecm_id}' not found"
    if ecm["state"] != "activated":
        return False, f"ECM '{ecm_id}' is not activated (state={ecm['state']})"

    # Unregister skills
    config = ecm["config"]
    for skill_name in config.get("skills", []):
        _skill_registry.pop(skill_name, None)

    ecm["state"] = "deactivated"
    return True, None


def uninstall_ecm(ecm_id):
    ecm = _ecm_registry.get(ecm_id)
    if not ecm:
        return False, f"ECM '{ecm_id}' not found"

    # Unregister skills if still active
    if ecm["state"] == "activated":
        config = ecm["config"]
        for skill_name in config.get("skills", []):
            _skill_registry.pop(skill_name, None)

    ecm["state"] = "uninstalled"
    return True, None


def register_skill(name, path, ecm_id):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _skill_registry[name] = {
        "module": module,
        "ecm_id": ecm_id,
    }


def get_skill(name):
    return _skill_registry.get(name)


def get_ecm_permissions(ecm_id):
    ecm = _ecm_registry.get(ecm_id)
    if not ecm:
        return {}
    return ecm.get("permissions", {})


def get_ecm(ecm_id):
    return _ecm_registry.get(ecm_id)


def list_skills():
    return list(_skill_registry.keys())


def list_ecms():
    return _ecm_registry
