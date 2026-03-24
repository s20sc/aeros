from eap.registry import get_eap_permissions
from runtime.system_policy import SYSTEM_POLICY

_blocked_skills = set()


def block_skill(name):
    _blocked_skills.add(name)


def unblock_skill(name):
    _blocked_skills.discard(name)


def check_permission(skill_name, eap_id):
    # Layer 1: operator override
    if skill_name in _blocked_skills:
        return False, "skill explicitly blocked by operator"

    # Layer 2: EAP-declared allowed_skills
    permissions = get_eap_permissions(eap_id)

    if not permissions:
        return False, f"EAP '{eap_id}' has no permissions declared"

    allowed_skills = permissions.get("allowed_skills", [])
    if skill_name not in allowed_skills:
        return False, f"skill '{skill_name}' not in allowed_skills of '{eap_id}'"

    # Layer 3: skill-level risk + actuator scope
    skill_permissions = permissions.get("skill_permissions", {})
    skill_policy = skill_permissions.get(skill_name, {})

    risk_level = skill_policy.get("risk_level", "low")
    if risk_level in SYSTEM_POLICY["blocked_risk_levels"]:
        return False, f"blocked_risk_level:{risk_level}"

    actuators = skill_policy.get("actuators", [])
    for actuator in actuators:
        if actuator not in SYSTEM_POLICY["allowed_actuators"]:
            return False, f"actuator_not_allowed:{actuator}"

    return True, None
