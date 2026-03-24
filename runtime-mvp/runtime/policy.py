import os
import yaml

_granted = {}  # eap_id -> list of permission dicts
_blocked_skills = set()


def load_permissions(eap_path, eap_id):
    perm_file = os.path.join(eap_path, "permissions.yaml")
    if not os.path.exists(perm_file):
        _granted[eap_id] = []
        return

    with open(perm_file) as f:
        config = yaml.safe_load(f)

    perms = config.get("permissions", [])
    _granted[eap_id] = perms

    for p in perms:
        print(f"[Runtime]  Granted: {p['type']}.{p['scope']} ({p.get('level', 'execute')})")


def block_skill(name):
    _blocked_skills.add(name)


def unblock_skill(name):
    _blocked_skills.discard(name)


def check_permission(skill_name):
    # Explicit block list takes priority
    if skill_name in _blocked_skills:
        return False, "skill explicitly blocked by policy"

    # Check if the skill belongs to any registered EAP
    skill_domain = skill_name.split(".")[0]
    domain_recognized = False

    for eap_id, perms in _granted.items():
        for p in perms:
            scope = p.get("scope", "")
            if skill_domain in scope or scope.startswith(f"{skill_domain}."):
                domain_recognized = True
                if p["type"] == "actuator":
                    return True, None

    # If no EAP recognizes this skill domain, deny it
    if not domain_recognized and _granted:
        return False, f"no EAP grants permission for '{skill_domain}'"

    return True, None
