# EAPOS

**Embodied Ability Package Operating System**

A capability-packaged operating architecture for embodied intelligent systems.

> **One Robot = One Persistent Agent. Capabilities = Installable Packages.**

### [Watch the Demo](https://youtu.be/5KdKa5meWgw)

[![EAPOS Demo](https://img.youtube.com/vi/5KdKa5meWgw/maxresdefault.jpg)](https://youtu.be/5KdKa5meWgw)

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              Persistent Agent               │
│         (sense → plan → act loop)           │
├─────────────────────────────────────────────┤
│              EAP Manager                    │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│   │ dumpling │ │pick_place│ │  clean   │   │
│   │ EAP      │ │ EAP      │ │  EAP     │   │
│   └──────────┘ └──────────┘ └──────────┘   │
├─────────────────────────────────────────────┤
│              Runtime Layer                  │
│  Policy ∙ Permissions ∙ Audit ∙ Trace      │
├─────────────────────────────────────────────┤
│          Perception + World State           │
├─────────────────────────────────────────────┤
│          Robot API (Mock / Gazebo)          │
├─────────────────────────────────────────────┤
│          Hardware / Simulation              │
└─────────────────────────────────────────────┘
```

---

## Quick Start

```bash
git clone https://github.com/s20sc/eapos-spec.git
cd eapos-spec
pip install -r requirements.txt
cd runtime-mvp
python main.py          # Interactive mode
bash demo.sh            # Or run the automated demo
```

```
EAPOS Runtime v1.0
Type "help" for commands

>>> make dumplings
>>> clean table
>>> pick up the cup
```

To launch the web UI (in a second terminal):

```bash
cd ui && python3 -m http.server 8000
# Open http://localhost:8000, click "Live Mode: ON"
```

---

## What It Does

### Dynamic Re-planning Loop

The agent doesn't execute a fixed script. It runs a **sense → plan → act** loop:

```
>>> make dumplings

[Agent]    === Re-plan cycle 1 ===
[Planner]  -> dumpling.prepare (materials needed)
[Planner]  -> dumpling.wrap (wrapping needed)
[Planner]  -> dumpling.boil (cooking needed)
[Planner]  Dynamic plan: 3 step(s)
[Agent]    Executing next: dumpling.prepare
[Robot]    Moving arm to 'dough_station'...
[Robot]    Grasping...

[Agent]    === Re-plan cycle 2 ===
[Planner]  -> dumpling.wrap (wrapping needed)    ← prepare done, skipped
[Planner]  -> dumpling.boil (cooking needed)
[Agent]    Executing next: dumpling.wrap
[Percept]  Workspace ready: True
[Percept]  Wrapper alignment check: aligned
[Robot]    Moving arm to 'dough'...

[Agent]    === Re-plan cycle 3 ===
[Planner]  -> dumpling.boil (cooking needed)     ← wrap done, skipped
[Agent]    Executing next: dumpling.boil

[Agent]    === Re-plan cycle 4 ===
[Planner]  Nothing to do — task already complete.
```

Each cycle: planner reads world state, generates only the steps still needed, executes one, then re-plans.

### Policy Enforcement (3 layers)

```
>>> cut with knife
[Runtime]  DENIED: unsafe.cut — blocked_risk_level:high

>>> block dumpling.wrap
[Runtime]  Blocked: dumpling.wrap
>>> make dumplings
[Agent]    Step 2 blocked by policy — task graph halted.
```

| Layer | Mechanism |
|-------|-----------|
| Operator override | `block` / `unblock` commands |
| EAP declaration | `allowed_skills` whitelist in permissions.yaml |
| System policy | Risk levels + actuator scope enforcement |

### Retry + Fallback + Recovery

```
[Skill]    ERROR: filling leaked during fold
[Agent]    Failed — retrying (2/3)
[Skill]    ERROR: filling leaked during fold — retrying (3/3)
[Agent]    Triggering fallback: dumpling.recover
[Skill]    Initiating recovery procedure...
[Skill]    Wrapper alignment corrected.
[Agent]    Recovery succeeded — continuing execution.
[Agent]    Step 3/3: dumpling.boil — OK
```

### EAP Lifecycle

```
>>> list
[*] com.eapos.dumpling     v3.0.0  activated
[*] com.eapos.pick_place   v1.0.0  activated
[*] com.eapos.clean_table  v1.0.0  activated
[x] com.eapos.unsafe       v1.0.0  uninstalled

>>> deactivate com.eapos.dumpling
>>> make dumplings
[Agent]    Skill not found — task blocked.
>>> activate com.eapos.dumpling
>>> make dumplings
[Agent]    Task complete.
```

### World State + Perception

Skills perceive the world before acting. The planner adapts based on what has changed.

```
>>> world
=== WORLD STATE ===
  robot_position: pot
  dumpling_cooked: True
  table_wiped: True
  table_organized: True
```

### Web UI — Live Dashboard

The Trace Viewer shows real-time execution with:

- **World State** panel — color-coded environment properties
- **Execution Flow** — node graph with retry/failure indicators
- **Mermaid Graph** — auto-generated flowchart
- **Timeline** — proportional duration bars per step
- **Step Details** — full state transition table
- **Replay** — step-by-step playback animation
- **Live Mode** — auto-refreshes as the runtime executes

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `<instruction>` | Run a task ("make dumplings", "clean table", "pick up the cup") |
| `list` | Show all EAPs with state, skills, permissions |
| `install <path>` | Install and activate an EAP |
| `activate <id>` | Activate a deactivated EAP |
| `deactivate <id>` | Deactivate (skills become unavailable) |
| `uninstall <id>` | Remove an EAP |
| `block <skill>` | Operator override: block a skill |
| `unblock <skill>` | Remove operator block |
| `world` | Inspect current world state |
| `audit` | View policy decision log |
| `trace` | View execution trace table |
| `trace viz` | Compact one-line execution graph |
| `trace mermaid` | Generate Mermaid flowchart |
| `trace save` | Export trace to JSON file |
| `trace json` | Print trace as JSON |

---

## Design Principles

### 1. Single-Agent Principle

Each robot contains exactly one persistent agent — the sole locus of decision-making, memory, and identity.

### 2. Capability Packaging

All capabilities are delivered through EAPs — modular, versioned, installable packages. A robot gains new abilities by installing EAPs, not by rewriting its core.

### 3. Policy-Logic Separation

Skills define *what* to do. The runtime defines *what is allowed*. No skill can bypass the runtime.

---

## Repository Structure

```
eapos-spec/
├── spec/           Architectural specifications
├── schemas/        Machine-readable JSON schemas
├── examples/       Reference EAP definitions (YAML)
├── runtime-mvp/    Working runtime implementation (Python)
│   ├── agent/        Agent + planner + re-planning loop
│   ├── eap/          EAP loader + registry + lifecycle
│   ├── runtime/      Policy, audit, trace, robot API, world state, perception
│   └── examples/     4 EAPs: dumpling, pick_place, clean_table, unsafe
├── ui/             Web-based trace viewer + live dashboard
└── docs/           Developer guide
```

---

## Relation to Paper

This repository provides the reference implementation for:

> *Toward Single-Agent Robots: A Capability-Packaged Operating Architecture (EAPOS)*

---

## License

MIT
