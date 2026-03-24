import os
import yaml
from eap.registry import register_skill, register_eap
from runtime.policy import load_permissions


def load_eap(path):
    manifest_path = os.path.join(path, "eap.yaml")

    with open(manifest_path) as f:
        config = yaml.safe_load(f)

    eap_id = config["id"]
    print(f"[EAP]      Loading: {eap_id} v{config['version']}")

    # Load permissions
    load_permissions(path, eap_id)

    # Register skills
    skills_dir = os.path.join(path, "skills")

    for skill_name in config.get("skills", []):
        module_file = skill_name.split(".")[-1] + ".py"
        module_path = os.path.join(skills_dir, module_file)

        if os.path.exists(module_path):
            register_skill(skill_name, module_path)
            print(f"[EAP]      Registered skill: {skill_name}")
        else:
            print(f"[EAP]      Warning: skill file not found: {module_path}")

    register_eap(eap_id, config)
    print(f"[EAP]      Loaded: {eap_id}")
