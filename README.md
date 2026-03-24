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
# Install an EAP
eapos install ./examples/dumpling_eap

# List installed capabilities
eapos list

# Run a task
eapos run "make a dumpling"

# Check logs
eapos logs
```

```
[Agent]    Received: "make a dumpling"
[Agent]    Planning task...
[Agent]    Selected EAP: com.eapos.dumpling
[Agent]    Dispatching skill: dumpling.plan
[Runtime]  Permission check: sensor.camera — OK
[Runtime]  Permission check: actuator.arm — OK
[Skill]    dumpling.plan — completed (1.2s)
[Agent]    Dispatching skill: dumpling.exec
[Skill]    dumpling.exec — completed (12.4s)
[Agent]    Task complete.
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
