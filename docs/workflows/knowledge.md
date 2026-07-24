# Knowledge and Coordination

Compound GPID stores decisions, plans, evidence, findings, and verified lessons
in project-controlled files. These artifacts complement version control; they
do not replace it.

## Capture a verified lesson

Run `/cg-compound` after a non-trivial problem has been solved and verified. It
writes a categorized solution under `.cg-docs/solutions/`. Do not capture a
speculative fix as settled knowledge.

Use `/cg-compound-refresh` to inspect solutions for staleness, drift, or useful
consolidation.

## Build and query the project Brain

`cg-index --brain` and `/cg-brain-rebuild` derive Brain indexes from committed
project artifacts. `cg-index query` performs bounded local retrieval without
requiring an external vector service. The optional retrieval registry does not
make other backends active.

## Coordinate work

- `@cg-roadmap` writes `roadmap.json`; `/cg-roadmap-view` renders progress.
- `/cg-issues` links optional GitHub Issues to roadmap work. The roadmap remains
  authoritative for feature status and plan links.
- `/cg-wiki` manages project wiki structure and generated sections according to
  ownership markers.
- Team Brain is an optional cross-project mechanism with its own repository and
  privacy configuration. See [Team Brain Schema](../team-brain-schema.md).

## Knowledge boundaries

- Keep secrets, credentials, raw private data, and unnecessary command output
  out of knowledge artifacts.
- Commit `.cg-docs/`; do not gitignore institutional knowledge.
- Keep temporary token-output evidence separate from durable solutions and
  decisions.
- Treat generated Brain files as indexes of source artifacts, not substitutes
  for those artifacts.

## Related pages

- [Files and Artifacts](../reference/files.md)
- [Institutional Knowledge Skills](../skills/institutional.md)
- [Detailed Workflow Manual](../workflow.md)
