# Blocked skills (for demo: shows runtime can deny execution)
_blocked = set()


def block_skill(name):
    _blocked.add(name)


def unblock_skill(name):
    _blocked.discard(name)


def check_permission(skill_name):
    if skill_name in _blocked:
        return False
    return True
