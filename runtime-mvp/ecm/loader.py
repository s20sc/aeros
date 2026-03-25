import os
import yaml
from ecm.registry import register_ecm, activate_ecm


def load_ecm(path):
    manifest_path = os.path.join(path, "ecm.yaml")

    try:
        with open(manifest_path) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"[ECM]      Error: manifest not found at {manifest_path}")
        return False
    except yaml.YAMLError as e:
        print(f"[ECM]      Error: malformed YAML in {manifest_path}: {e}")
        return False

    if not config or "id" not in config:
        print(f"[ECM]      Error: missing 'id' in manifest {manifest_path}")
        return False

    ecm_id = config["id"]
    print(f"[ECM]      Installing: {ecm_id} v{config['version']}")

    # Load permissions
    perm_path = os.path.join(path, "permissions.yaml")
    permissions = {}
    if os.path.exists(perm_path):
        with open(perm_path) as f:
            permissions = yaml.safe_load(f) or {}

    # Show skill-level permissions
    skill_perms = permissions.get("skill_permissions", {})
    for sk, sp in skill_perms.items():
        acts = sp.get("actuators", [])
        risk = sp.get("risk_level", "low")
        print(f"[ECM]        {sk}: actuators={acts}, risk={risk}")

    # Register EAP (state: installed)
    register_ecm(ecm_id, config, permissions, os.path.abspath(path))
    print(f"[ECM]      Installed: {ecm_id}")

    # Auto-activate
    ok, err = activate_ecm(ecm_id)
    if ok:
        skills = config.get("skills", [])
        for s in skills:
            print(f"[ECM]      Registered skill: {s}")
        print(f"[ECM]      Activated: {ecm_id}")
    else:
        print(f"[ECM]      Activation failed: {err}")
