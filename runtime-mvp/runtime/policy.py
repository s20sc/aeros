from eap.registry import get_eap_permissions

_blocked_skills = set()


def block_skill(name):
    _blocked_skills.add(name)


def unblock_skill(name):
    _blocked_skills.discard(name)


def check_permission(skill_name, eap_id):
    # Manual block list takes highest priority
    if skill_name in _blocked_skills:
        return False, "skill explicitly blocked by operator"

    # Look up EAP's declared permissions
    permissions = get_eap_permissions(eap_id)

    if not permissions:
        return False, f"EAP '{eap_id}' has no permissions declared"

    # Check allowed_skills whitelist
    allowed_skills = permissions.get("allowed_skills", [])

    if skill_name not in allowed_skills:
        return False, f"skill '{skill_name}' not in allowed_skills of '{eap_id}'"

    # Check risk level
    risk = permissions.get("risk_level", "unknown")
    if risk == "critical":
        return False, f"EAP '{eap_id}' has risk_level=critical, requires manual approval"

    return True, None
