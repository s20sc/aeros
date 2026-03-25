# ECM Schema Specification

## Definition

An Embodied Capability Module (ECM) is a structured, installable unit that provides capabilities to a persistent agent.

## Abstract Model

An ECM is defined as:

```
E = (C, S, M, P, D)
```

Where:

- C: capability definitions
- S: skills
- M: models/tools
- P: permissions
- D: metadata and dependencies

---

## Required Components

### 1. Manifest (ecm.yaml)

Defines:

- identity
- version
- capabilities
- entrypoints
- resource requirements

---

### 2. Skills

Executable units with:

- input/output schema
- preconditions
- postconditions
- cost model

---

### 3. Permissions

Declares:

- sensor access
- actuator control
- data scope
- network access

---

## Key Constraints

- ECM MUST NOT contain agent-level constructs
- ECM MUST NOT maintain persistent identity
- ECM MUST be invoked by the agent

---

## Execution Model

```
Agent -> Skill -> Runtime -> Hardware
```
