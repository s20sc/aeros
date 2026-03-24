import json
import datetime
import os

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


def save_trace(directory="."):
    trace = get_trace()
    if not trace:
        print("[Trace]    No trace to export.")
        return None

    ts = trace.get("started_at", "unknown").replace(":", "-")
    filename = f"trace_{ts}.json"
    filepath = os.path.join(directory, filename)

    with open(filepath, "w") as f:
        json.dump(trace, f, indent=2)

    print(f"[Trace]    Exported to {filepath}")
    return filepath


def generate_mermaid():
    """Generate a Mermaid flowchart from the execution trace."""
    trace = get_trace()
    if not trace:
        print("No execution trace yet.\n")
        return None

    # Collect final status per step_id
    step_results = {}
    for entry in trace["steps"]:
        sid = entry["id"]
        if sid not in step_results:
            step_results[sid] = {
                "skill": entry["skill"],
                "status": "running",
                "reason": None,
                "attempts": 0,
            }
        step_results[sid]["status"] = entry["status"]
        step_results[sid]["reason"] = entry.get("reason")
        if entry["status"] in ("running",):
            step_results[sid]["attempts"] += 1

    lines = ["graph LR"]
    ordered = list(step_results.items())

    for i, (sid, info) in enumerate(ordered):
        skill = info["skill"].replace(".", "_")
        label = info["skill"]
        status = info["status"]

        if status == "success":
            style = ":::success"
            label_extra = ""
        elif status == "failed":
            style = ":::failed"
            reason = info.get("reason") or "failed"
            label_extra = f"\\n{reason}"
        else:
            style = ""
            label_extra = ""

        attempts = info["attempts"]
        if attempts > 1:
            label_extra += f"\\n({attempts} attempts)"

        node_id = f"{sid}_{skill}"
        lines.append(f"    {node_id}[\"{label}{label_extra}\"]")

        if i > 0:
            prev_sid, prev_info = ordered[i - 1]
            prev_skill = prev_info["skill"].replace(".", "_")
            prev_node = f"{prev_sid}_{prev_skill}"

            # Recovery step gets a dotted arrow
            if "_recovery" in sid:
                lines.append(f"    {prev_node} -.->|fallback| {node_id}")
            else:
                lines.append(f"    {prev_node} --> {node_id}")

    # Style classes
    lines.append("")
    lines.append("    classDef success fill:#2d6,stroke:#1a4,color:#fff")
    lines.append("    classDef failed fill:#d33,stroke:#a11,color:#fff")

    # Apply styles
    for sid, info in step_results.items():
        skill = info["skill"].replace(".", "_")
        node_id = f"{sid}_{skill}"
        if info["status"] == "success":
            lines.append(f"    class {node_id} success")
        elif info["status"] == "failed":
            lines.append(f"    class {node_id} failed")

    mermaid = "\n".join(lines)
    return mermaid
