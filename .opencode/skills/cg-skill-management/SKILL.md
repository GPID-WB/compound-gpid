---
name: cg-skill-management
description: "Internal contracts and workflows for the private Compound GPID skill-management dispatcher."
---

# Skill Management

This internal bundle owns the contracts and focused workflows for the private
skill-management implementation. It does not register a public capability or a
public command. Public registration occurs only after the complete release gate.

## Common State Vocabulary

Keep these values identical in contracts, Python constants, fixtures, and tests.

- Origin: plugin-canonical, project-imported
- Admission: quarantined, approved, rejected
- Lifecycle: current, deprecated, removed
- Availability: inactive, active
- Manifest health: fresh, missing, stale, invalid

Consumer is the default role. Maintainer writes require the invocation Git root,
project root, and canonical source root to identify the same approved development
checkout on a non-detached, nondefault, nonprotected feature branch.
