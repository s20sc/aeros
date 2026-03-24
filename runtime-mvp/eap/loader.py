import os
import yaml
from eap.registry import register_skill, register_eap


def load_eap(path):
    manifest_path = os.path.join(path, "eap.yaml")

    with open(manifest_path) as f:
        config = yaml.safe_load(f)

    eap_id = config["id"]
    print(f"[EAP]      Loading: {eap_id} v{config['version']}")

    # Load permissions
    perm_path = os.path.join(path, "permissions.yaml")
    permissions = {}
    if os.path.exists(perm_path):
        with open(perm_path) as f:
            permissions = yaml.safe_load(f) or {}

    allowed = permissions.get("allowed_skills", [])
    skill_perms = permissions.get("skill_permissions", {})
    print(f"[EAP]      Allowed skills: {allowed}")
    for sk, sp in skill_perms.items():
        acts = sp.get("actuators", [])
        risk = sp.get("risk_level", "low")
        print(f"[EAP]        {sk}: actuators={acts}, risk={risk}")

    # Register EAP with permissions
    register_eap(eap_id, config, permissions)

    # Register skills
    skills_dir = os.path.join(path, "skills")

    for skill_name in config.get("skills", []):
        module_file = skill_name.split(".")[-1] + ".py"
        module_path = os.path.join(skills_dir, module_file)

        if os.path.exists(module_path):
            register_skill(skill_name, module_path, eap_id)
            print(f"[EAP]      Registered skill: {skill_name}")
        else:
            print(f"[EAP]      Warning: skill file not found: {module_path}")

    print(f"[EAP]      Loaded: {eap_id}")
