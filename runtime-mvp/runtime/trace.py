import json
import datetime

_current_trace = None


def start_trace(task_name):
    global _current_trace
    _current_trace = {
        "task": task_name,
        "started_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "steps": [],
        "result": "running",
    }


def add_step(step_id, skill_name, status, reason=None, attempt=1):
    if _current_trace is None:
        return
    _current_trace["steps"].append({
        "id": step_id,
        "skill": skill_name,
        "status": status,
        "reason": reason,
        "attempt": attempt,
        "time": datetime.datetime.now().isoformat(timespec="seconds"),
    })


def finish_trace(result):
    if _current_trace is None:
        return
    _current_trace["result"] = result
    _current_trace["finished_at"] = datetime.datetime.now().isoformat(timespec="seconds")


def get_trace():
    return _current_trace


def print_trace():
    trace = get_trace()
    if not trace:
        print("No execution trace yet.\n")
        return

    print(f"\n=== EXECUTION TRACE ===")
    print(f"Task: {trace['task']}  result={trace['result']}")
    print(f"Started: {trace.get('started_at', '?')}  Finished: {trace.get('finished_at', '?')}")
    print()

    for entry in trace["steps"]:
        reason_str = f"  reason={entry['reason']}" if entry.get("reason") else ""
        print(f"  {entry['id']:20s} {entry['skill']:25s} status={entry['status']:10s} attempt={entry['attempt']}{reason_str}")
    print()


def export_trace_json():
    trace = get_trace()
    if not trace:
        print("No execution trace yet.\n")
        return None
    return json.dumps(trace, indent=2)
