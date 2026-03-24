import os
import yaml
from eap.registry import register_eap, activate_eap


def load_eap(path):
    manifest_path = os.path.join(path, "eap.yaml")

    with open(manifest_path) as f:
        config = yaml.safe_load(f)

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
