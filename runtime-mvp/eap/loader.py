import os
import yaml
from eap.registry import register_eap, activate_eap


def load_eap(path):
    manifest_path = os.path.join(path, "eap.yaml")

    try:
        with open(manifest_path) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"[EAP]      Error: manifest not found at {manifest_path}")
        return False
    except yaml.YAMLError as e:
        print(f"[EAP]      Error: malformed YAML in {manifest_path}: {e}")
        return False

    if not config or "id" not in config:
        print(f"[EAP]      Error: missing 'id' in manifest {manifest_path}")
        return False

    eap_id = config["id"]
    print(f"[EAP]      Installing: {eap_id} v{config['version']}")

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
        print(f"[EAP]        {sk}: actuators={acts}, risk={risk}")

    # Register EAP (state: installed)
    register_eap(eap_id, config, permissions, os.path.abspath(path))
    print(f"[EAP]      Installed: {eap_id}")

    # Auto-activate
    ok, err = activate_eap(eap_id)
    if ok:
        skills = config.get("skills", [])
        for s in skills:
            print(f"[EAP]      Registered skill: {s}")
        print(f"[EAP]      Activated: {eap_id}")
    else:
        print(f"[EAP]      Activation failed: {err}")
