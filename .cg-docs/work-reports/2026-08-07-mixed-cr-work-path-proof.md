---
date: 2026-08-07
plan: ".cg-docs/plans/2026-08-07-modular-compound-gpid.md"
kind: integration-evidence
status: completed
---

# Mixed /cr-work Integration Proof (V10 / R8)

## Objective

Demonstrate one complete mixed `/cr-work` path that uses research reasoning
(a cr-agent), R implementation (a capability-pack skill), testing and
reproducibility (capability packs), and publication output (a capability pack) —
with **no direct dependency on the technical suite**. This is the architectural
proof that modular boundaries hold under real use.

## Path Under Test

`/cr-work` (prompt: `.github/prompts/cr-work.prompt.md`) performs research
workflow orchestration. Its conditional skill loads pull from both the research
suite's domain skills and shared capability packs:

| Dependency | Owning module | Layer | Loaded via |
|---|---|---|---|
| `cr-skill-research-workflow` | `suite-cr` | suite | research workflow convention |
| `cr-skill-research-integrity` | `suite-cr` | suite | P0 silent-error catalog |
| `cr-skill-research-scoping` | `suite-cr` | suite | normative-decision taxonomy |
| `cr-skill-evidence-provenance` | `suite-cr` | suite | evidence provenance protocol |
| `cr-skill-mathematical-derivation` | `cap-language-research` | capability | derivation conventions |
| `cr-skill-measurement` | `suite-cr` | suite | measurement/classification |
| `cr-skill-publication-output` | `cap-research-output` | capability | regression/LateX output primitives |
| `cr-skill-replication-standards` | `cap-research-output` | capability | reproducibility/replication |
| `.github/instructions/r.instructions.md` | `cap-language-r` | capability | R implementation style |
| `.github/shared/context-loading.contract.md` | `kernel` | kernel | staged context-loading |

## Dependency Resolution

- The `/cr-work` prompt's requirement "Always load `cr-skill-research-workflow`,
  `cr-skill-research-integrity`, `cr-skill-research-scoping`, and
  `cr-skill-evidence-provenance`" resolves to `suite-cr` (self-owned).
- Tables/Figures mode loads `cr-skill-publication-output` ↔ `cap-research-output`
  (capability pack).
- Reproducibility mode loads `cr-skill-replication-standards` ↔
  `cap-research-output` (capability pack).
- Implementation mode resolves derivation conventions through
  `cr-skill-mathematical-derivation` ↔ `cap-language-research` (capability pack).
- Context staging resolves through `.github/shared/context-loading.contract.md`
  ↔ `kernel`.

Note: `/.github/instructions/r.instructions.md` is a capability-pack asset
(`cap-language-r`) that applies in research implementation mode via the platform
auto-applying language instruction files; it is not directly referenced by the
`/cr-work` prompt body itself.

None of the resolved owned-asset references resolve to `.github/prompts/cg-*`,
`.github/agents/cg-*`, or any asset owned by `suite-cg`. The technical suite's
assets are not on this path (though `/cr-work` behaviorally defers to `/cg-work`
conventions for plan loading and phase parsing, which is a documentation-level
delegation, not an owned-asset dependency).

## Enforcement

`python scripts/cg_validate_modules.py --check-cross-suite` exits 0 on the real
registry (R4/V9): no `cr-*` asset references a `cg-*` asset owned by the technical
suite except through shared capability packs (`cap-language-r`, etc.).

`pytest scripts/tests/test_target_drift.py` (via `TestCrCgParity`) proves the
same CR assets emit to all five platform trees.

## Result

The mixed `/cr-work` path resolves entirely through kernel and capability packs
plus the research suite's own domain skills. No owned-asset reference resolves
to `suite-cg`: the cross-suite gate confirms no direct technical-suite
dependency — **proof complete**.
