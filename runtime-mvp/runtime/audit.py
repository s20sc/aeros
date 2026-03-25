import datetime

_log = []


def record(skill_name, ecm_id, decision, reason=None):
    entry = {
        "time": datetime.datetime.now().isoformat(timespec="seconds"),
        "skill": skill_name,
        "ecm": ecm_id,
        "decision": decision,
        "reason": reason,
    }
    _log.append(entry)

    reason_str = f" reason={reason}" if reason else ""
    print(f"[Audit]    skill={skill_name} ecm={ecm_id} decision={decision}{reason_str}")


def get_log():
    return list(_log)
