# Developer Guide

## Prerequisites

- Python 3.8+
- pyyaml (`pip install pyyaml`)

## Quick Start

```bash
git clone https://github.com/s20sc/aeros.git
cd aeros/runtime-mvp
pip install -r ../requirements.txt
python main.py
```

## How to Build an ECM

An ECM (Embodied Capability Module) is a folder with this structure:

```
my_ecm/
├── ecm.yaml           # Manifest: id, version, skills list
├── permissions.yaml   # Allowed skills, actuators, risk levels
└── skills/
    ├── plan.py        # Planning skill (reads world state, returns task graph)
    └── action.py      # Action skill (calls robot API, updates world)
```

### 1. Define ecm.yaml

```yaml
id: com.aeros.my_task
version: 1.0.0
description: My custom capability

skills:
  - my_task.plan
  - my_task.action
```

### 2. Declare permissions

```yaml
allowed_skills:
  - my_task.plan
  - my_task.action

skill_permissions:
  my_task.plan:
    actuators: []
    risk_level: low
  my_task.action:
    actuators:
      - arm
      - gripper
    risk_level: low
```

### 3. Write skills

Every skill is a Python file with a `run()` function that returns a status dict:

```python
# skills/action.py
def run():
    # Your logic here
    return {"status": "success"}
```

Plan skills return a task graph:

```python
# skills/plan.py
def run():
    return {
        "status": "success",
        "task_graph": {
            "task": "my_task",
            "steps": [
                {"skill": "my_task.action"},
            ]
        }
    }
```

Skills can use the robot API and world state:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.robot.context import robot
from runtime.world.context import world

def run():
    robot.move_arm("target")
    robot.grasp()
    world.my_custom_flag = True
    return {"status": "success"}
```

### 4. Install and run

```
>>> install ./path/to/my_ecm
>>> my task instruction
```

## Task Graph Features

Steps support retry, fallback, and recovery:

```python
{
    "skill": "my_task.risky_step",
    "retry": 2,                          # Retry up to 2 times
    "on_failure": "my_task.recover",     # Fallback skill
    "continue_on_recovery": True         # Resume after recovery
}
```

## Running the Automated Demo

```bash
cd runtime-mvp
bash demo.sh
```

## Web UI

Start the UI server in a separate terminal:

```bash
cd ui
python3 -m http.server 8000
```

Open http://localhost:8000 and click "Live Mode: ON" to see real-time execution traces.
