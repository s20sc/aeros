# EAPOS Specification

**Embodied Ability Package Operating System (EAPOS)**

EAPOS is a capability-packaged operating architecture for embodied intelligent systems.

It defines a new computational model:

> **One Robot = One Persistent Agent**
> **Capabilities = Installable Packages (EAPs)**

---

## Architecture

```
┌─────────────────────────────────────────────┐
│                   Agent                     │
│          (Single Persistent Subject)        │
├─────────────────────────────────────────────┤
│              EAP Manager                    │
│    ┌─────────┐ ┌─────────┐ ┌─────────┐     │
│    │ EAP: A  │ │ EAP: B  │ │ EAP: C  │     │
│    │┌───────┐│ │┌───────┐│ │┌───────┐│     │
│    ││ skill ││ ││ skill ││ ││ skill ││     │
│    │└───────┘│ │└───────┘│ │└───────┘│     │
│    └─────────┘ └─────────┘ └─────────┘     │
├─────────────────────────────────────────────┤
│              Runtime Layer                  │
│  ┌──────────┐ ┌───────────┐ ┌───────────┐  │
│  │ Policy   │ │ Permission│ │ Execution  │  │
│  │ Engine   │ │ Guard     │ │ Scheduler  │  │
│  └──────────┘ └───────────┘ └───────────┘  │
├─────────────────────────────────────────────┤
│           Hardware / Simulation             │
│     sensors    actuators    world model     │
└─────────────────────────────────────────────┘
```

---

## Quick Start

```bash
cd runtime-mvp
pip install pyyaml
python main.py
```

### Demo 1: Resilient task graph — retry + fallback + continue (EAP: dumpling)

The plan skill generates a structured task graph. Steps support `retry`, `on_failure` (fallback), and `continue_on_recovery` (resume after recovery).

```
Task graph:
  -> dumpling.prepare
  -> dumpling.wrap [retry=2, fallback=dumpling.recover, continue_on_recovery]
  -> dumpling.boil
```

**Path A — success on first try:**

```
Step 1/3: dumpling.prepare — OK
Step 2/3: dumpling.wrap — OK
Step 3/3: dumpling.boil — OK
All steps complete. Task done.
```

**Path B — retry succeeds:**

```
Step 2/3: dumpling.wrap
[Skill]    ERROR: filling leaked during fold
[Agent]    Step 2 failed — retrying (2/3)
[Skill]    Dumpling wrapped.
Step 3/3: dumpling.boil — OK
All steps complete. Task done.
```

**Path C — all retries fail, fallback triggered, execution continues:**

```
Step 2/3: dumpling.wrap
[Skill]    ERROR: filling leaked during fold — retrying (2/3)
[Skill]    ERROR: filling leaked during fold — retrying (3/3)
[Skill]    ERROR: filling leaked during fold
[Agent]    Step 2 failed after 3 attempt(s): wrap_integrity_check_failed
[Agent]    Triggering fallback: dumpling.recover
[Skill]    Initiating recovery procedure...
[Skill]    Recovery complete — ready for retry.
[Agent]    Recovery succeeded — continuing execution.
Step 3/3: dumpling.boil — OK
All steps complete. Task done.
```

### Demo 2: Pick up a cup (EAP: pick_place)

```
>>> pick up the cup
[Agent]    Received: "pick up the cup"
[Agent]    Planning task...
[Agent]    Dispatching skill: pick_place.detect
[Runtime]  Permission check: pick_place.detect (from com.eapos.pick_place)
[Runtime]  Permission — OK
[Skill]    Scanning workspace with RGB-D camera...
[Skill]    Detected: red_cup at (0.35, 0.12, 0.08)
[Agent]    Dispatching skill: pick_place.grasp
[Runtime]  Permission check: pick_place.grasp (from com.eapos.pick_place)
[Runtime]  Permission — OK
[Skill]    Computing grasp pose...
[Skill]    Gripper closed — object secured
[Agent]    Dispatching skill: pick_place.place
[Runtime]  Permission check: pick_place.place (from com.eapos.pick_place)
[Runtime]  Permission — OK
[Skill]    Gripper open — object placed
[Agent]    Task complete.
```

### Demo 3: Policy denial — risk level blocked by system policy

The `unsafe_eap` declares `unsafe.cut` as allowed, but with `risk_level: high`.
The system policy blocks all high-risk skills. The skill is installed — **but the runtime refuses**.

```
>>> cut with knife
[Agent]    Received: "cut with knife"
[Agent]    Dispatching skill: unsafe.cut
[Runtime]  Permission check: unsafe.cut (from com.eapos.unsafe)
[Runtime]  DENIED: unsafe.cut — blocked_risk_level:high
[Audit]    skill=unsafe.cut eap=com.eapos.unsafe decision=deny reason=blocked_risk_level:high
[Agent]    Task blocked by policy.
```

If the risk block is lifted, the skill is **still denied** because `knife` is not in the system's allowed actuator list:

```
[Runtime]  DENIED: unsafe.cut — actuator_not_allowed:knife
```

### Demo 4: Graph halted mid-execution by policy

An operator blocks `dumpling.wrap`. The plan runs, step 1 succeeds, but step 2 is denied — the entire graph halts.

```
>>> block dumpling.wrap
[Runtime]  Blocked: dumpling.wrap

>>> make dumplings
[Agent]    Task graph received: 3 steps
[Agent]    Step 1/3: dumpling.prepare
[Runtime]  Permission check: dumpling.prepare — OK
[Skill]    Dough and filling ready.
[Agent]    Step 2/3: dumpling.wrap
[Runtime]  Permission check: dumpling.wrap (from com.eapos.dumpling)
[Runtime]  DENIED: dumpling.wrap — skill explicitly blocked by operator
[Agent]    Step 2 blocked by policy — task graph halted.
```

### Demo 5: EAP lifecycle — deactivate / activate / uninstall

```
>>> list
[*] EAP: com.eapos.dumpling    state: activated
[*] EAP: com.eapos.pick_place  state: activated
[*] EAP: com.eapos.unsafe      state: activated

>>> deactivate com.eapos.dumpling
[EAP]      Deactivated: com.eapos.dumpling

>>> make a dumpling
[Agent]    Skill not found: dumpling.plan
[Agent]    Task blocked — skill not installed.

>>> activate com.eapos.dumpling
[EAP]      Activated: com.eapos.dumpling

>>> make a dumpling
[Agent]    Task complete.

>>> uninstall com.eapos.unsafe
[EAP]      Uninstalled: com.eapos.unsafe

>>> list
[*] EAP: com.eapos.dumpling    state: activated
[*] EAP: com.eapos.pick_place  state: activated
[x] EAP: com.eapos.unsafe      state: uninstalled
```

### Demo 6: Detailed package inspection

```
>>> list
[*] EAP: com.eapos.dumpling
    version: 1.0.0
    state:   activated
    skills:
      - dumpling.plan (active)
      - dumpling.exec (active)
    permissions:
      dumpling.plan: risk=low, actuators=[]
      dumpling.exec: risk=low, actuators=['arm', 'gripper']
```

### Demo 7: Audit log

Every allow/deny decision is recorded with timestamp, skill, EAP, and reason.

```
>>> audit
Audit Log:
  1. [2026-03-24T14:39:40] skill=dumpling.plan eap=com.eapos.dumpling decision=allow
  2. [2026-03-24T14:39:41] skill=dumpling.exec eap=com.eapos.dumpling decision=allow
  3. [2026-03-24T14:39:42] skill=unsafe.cut eap=com.eapos.unsafe decision=deny reason=blocked_risk_level:high
```

---

## What is EAPOS?

EAPOS is not a framework, and not a middleware.

It is an operating model for robots:

- A robot is a single persistent intelligent subject
- Capabilities are modular, installable packages
- Execution is governed by a policy-enforced runtime

---

## Why EAPOS?

Existing robotic systems suffer from:

- fragmented control authority
- poor capability reuse
- tight coupling between logic and execution

EAPOS introduces:

- unified agent-centric control
- capability-level modularity
- system-level safety enforcement

---

## Design Principles

### 1. Single-Agent Principle

Each robot contains exactly one persistent agent. The agent is the sole locus of decision-making, memory, and identity. There are no competing controllers — only one subject that reasons, plans, and acts.

### 2. Capability Packaging Principle

All capabilities are delivered through EAPs — modular, versioned, installable packages. A robot gains new abilities by installing EAPs, not by rewriting its core. Skills, models, and tools are composed, not hardcoded.

### 3. Policy-Logic Separation

Skills define *what* to do. The runtime defines *what is allowed*. Execution constraints (permissions, safety bounds, resource limits) are enforced by the system, not by individual skills. No skill can bypass the runtime.

---

## Core Components

| Component | Description |
|-----------|-------------|
| Agent     | The single persistent intelligent subject |
| EAP       | Capability packages (skills, tools, models) |
| Runtime   | Execution + policy enforcement layer |

---

## Repository Structure

- `/spec` — conceptual and architectural specifications
- `/schemas` — machine-readable definitions
- `/examples` — reference capability packages
- `/runtime-mvp` — minimal viable runtime (Python)
- `/ui` — web-based trace viewer (load JSON, Mermaid graph)
- `/docs` — developer guides

---

## Example EAP

```yaml
id: com.eapos.dumpling
version: 1.0.0
skills:
  - dumpling.plan
  - dumpling.exec
resources:
  cpu: medium
  gpu: optional
```

---

## Status

Draft v0.1 — early-stage specification

---

## Relation to Paper

This repository provides the reference specification for:

> *Toward Single-Agent Robots: A Capability-Packaged Operating Architecture (EAPOS)*

---

## Vision

EAPOS aims to become:

> **The operating standard for capability-driven robots.**

---

## License

MIT
