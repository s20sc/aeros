# Skill Specification

## Definition

A Skill is the smallest executable unit within an EAP. It represents a single, well-defined capability that the agent can invoke.

## Structure

Each skill declares:

- **name**: unique identifier within the EAP
- **inputs**: typed input parameters
- **outputs**: typed output schema
- **preconditions**: world state requirements before execution
- **postconditions**: expected world state after execution
- **timeout_ms**: maximum execution time in milliseconds
- **retry**: number of allowed retries on failure

---

## Skill Lifecycle

```
Registered -> Activated -> Invoked -> Running -> Completed | Failed
```

---

## Composition

Skills can be composed into task graphs:

- **Sequential**: skill A then skill B
- **Parallel**: skill A and skill B concurrently
- **Conditional**: skill A if condition, else skill B

---

## Constraints

- A skill MUST NOT maintain state across invocations
- A skill MUST declare all required permissions
- A skill MUST be idempotent where possible
- A skill MUST NOT directly invoke other skills (composition is handled by the agent)
