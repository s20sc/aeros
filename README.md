# EAPOS Specification

**Embodied Ability Package Operating System (EAPOS)**

EAPOS is a capability-packaged operating architecture for embodied intelligent systems.

It defines a new computational model:

> **One Robot = One Persistent Agent**
> **Capabilities = Installable Packages (EAPs)**

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

## Example

```yaml
id: com.eapos.dumpling
version: 1.0.0
skills:
  - dumpling.plan
  - dumpling.exec
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
