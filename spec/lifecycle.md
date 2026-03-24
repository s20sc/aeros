# EAP Lifecycle

## States

An EAP transitions through the following states:

```
Packaged -> Installed -> Activated -> Running -> Deactivated -> Uninstalled
```

---

## State Descriptions

| State        | Description |
|--------------|-------------|
| Packaged     | EAP is bundled and ready for distribution |
| Installed    | EAP is present on the agent's runtime |
| Activated    | EAP skills are registered and available |
| Running      | One or more skills are currently executing |
| Deactivated  | EAP skills are unregistered but files remain |
| Uninstalled  | EAP is fully removed from the runtime |

---

## Transitions

- **Install**: validate manifest, check dependencies, copy to runtime
- **Activate**: register skills, grant declared permissions
- **Invoke**: agent triggers a skill execution
- **Deactivate**: unregister skills, revoke permissions
- **Uninstall**: remove all EAP files and metadata

---

## Constraints

- Only one version of an EAP may be active at a time
- Activation requires all declared permissions to be grantable
- Running skills must complete or be terminated before deactivation
