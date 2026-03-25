# ECM Lifecycle

## States

An ECM transitions through the following states:

```
Packaged -> Installed -> Activated -> Running -> Deactivated -> Uninstalled
```

---

## State Descriptions

| State        | Description |
|--------------|-------------|
| Packaged     | ECM is bundled and ready for distribution |
| Installed    | ECM is present on the agent's runtime |
| Activated    | ECM skills are registered and available |
| Running      | One or more skills are currently executing |
| Deactivated  | ECM skills are unregistered but files remain |
| Uninstalled  | ECM is fully removed from the runtime |

---

## Transitions

- **Install**: validate manifest, check dependencies, copy to runtime
- **Activate**: register skills, grant declared permissions
- **Invoke**: agent triggers a skill execution
- **Deactivate**: unregister skills, revoke permissions
- **Uninstall**: remove all ECM files and metadata

---

## Constraints

- Only one version of an ECM may be active at a time
- Activation requires all declared permissions to be grantable
- Running skills must complete or be terminated before deactivation
