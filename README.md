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

### Demo 1: Make a dumpling (EAP: dumpling)

```
>>> make a dumpling
[Agent]    Received: "make a dumpling"
[Agent]    Planning task...
[Agent]    Dispatching skill: dumpling.plan
[Runtime]  Permission check: dumpling.plan (from com.eapos.dumpling)
[Runtime]  Permission — OK
[Runtime]  Executing: dumpling.plan
[Skill]    Analyzing instruction...
[Skill]    Task graph generated:
[Skill]      step 1: prepare_dough
[Skill]      step 2: add_filling (after step 1)
[Skill]      step 3: wrap (after step 2)
[Skill]      step 4: steam (after step 3)
[Skill]    dumpling.plan — completed (0.3s)
[Agent]    Dispatching skill: dumpling.exec
[Runtime]  Permission check: dumpling.exec (from com.eapos.dumpling)
[Runtime]  Permission — OK
[Runtime]  Executing: dumpling.exec
[Skill]    Picking up dough...
[Skill]    Wrapping filling...
[Skill]    Shaping dumpling...
[Skill]    Placing on tray...
[Skill]    Dumpling complete.
[Skill]    dumpling.exec — completed (0.8s)
[Agent]    Task complete.
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

### Demo 4: Operator override — block a previously allowed skill

Even if an EAP declares a skill as allowed, an operator can block it at runtime.

```
>>> block dumpling.exec
[Runtime]  Blocked: dumpling.exec

>>> make a dumpling
[Agent]    Dispatching skill: dumpling.exec
[Runtime]  Permission check: dumpling.exec (from com.eapos.dumpling)
[Runtime]  DENIED: dumpling.exec — skill explicitly blocked by operator
[Audit]    skill=dumpling.exec eap=com.eapos.dumpling decision=deny reason=skill explicitly blocked by operator
[Agent]    Task blocked by policy.
```

### Demo 5: Audit log

Every allow/deny decision is recorded with timestamp, skill, EAP, and reason.

```
>>> audit
Audit Log:
  [2026-03-24T14:35:16] skill=dumpling.plan eap=com.eapos.dumpling decision=allow
  [2026-03-24T14:35:16] skill=dumpling.exec eap=com.eapos.dumpling decision=allow
  [2026-03-24T14:35:17] skill=pick_place.detect eap=com.eapos.pick_place decision=allow
  [2026-03-24T14:35:18] skill=unsafe.cut eap=com.eapos.unsafe decision=deny reason=blocked_risk_level:high
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
