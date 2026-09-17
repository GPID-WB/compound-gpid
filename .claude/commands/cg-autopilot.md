---
description: "Coordinate Kilo autopilot bootstrap probes; production execution is not enabled."
---

# Autopilot

Read `compound-gpid.md`, `compound-gpid.local.md` and
`.claude/shared/autopilot-stage.contract.md` before action. Apply its authority,
support, closed bootstrap protocol and evidence limits.

This command is probe-only. In Copilot, Claude Code, Codex or OpenCode, including
direct canonical entry, return `blocked: unsupported-adapter` and stop without
dispatch or effects. Never infer Kilo from an envelope or document flag.

On Kilo, require actual native selection of the installed dedicated primary
`cg-autopilot`. If unavailable, return `blocked: native-identity-unverified`.
Only an explicitly authorized read-only bootstrap request can proceed under the
contract. No production invocation is enabled: return
`blocked: bootstrap-only` for fresh/resume pipeline arguments. Runtime and
control preflight must be implemented and verified before production execution.
Do not create a marker, report, cursor, commit or other file from this stub.

Keep ordinary `/cg-work` and other commands unchanged. Never implement fixes or
run tests in the parent. No model advice becomes an assignment or tool override.

## Read-only helper surface (enabled)

The installed control helper supports exactly one enabled operation today:

```text
cg-autopilot-control inspect --root <repo> [--plan <path>] [--batches <segments>]
                              [--base <branch>] [--ci-timeout 30m]
                              [--resume .cg-docs/active-state/current.json]
```

`inspect` never writes. It returns one JSON report on stdout with
`"status": "eligible"` or `"status": "blocked"` plus a normalized run
specification or typed blockers. A completed inspection exits 0 for either
status; callers must inspect `status` and `blockers`, not infer eligibility
from the exit code. Invocation errors exit 1 without a report.
Diagnostics go to stderr as `cg-autopilot: <error-code>: <message>`; machine
stdout and diagnostics stay separate. An explicit `--root` is always required:
the helper never derives a project root from its installation directory and
never changes the consumer working directory. `--ci-timeout` takes a positive
integer with `s`, `m` or `h`, from 1 second through 24 hours; `--plan`,
`--batches` and `--base` are mutually exclusive with `--resume`.

All other helper operations (`prepare`, `begin-stage`, `begin-effect`,
`record-result`, `validate-stage`, `checkpoint`, `reconcile`, `observe-ci`,
`extend-ci-deadline`) answer `operation-not-implemented` with exit 1. They are
specified in `.claude/shared/autopilot-stage.contract.md` and documented in
`docs/reference.md` under the Autopilot section; they become available only
after native qualification completes. Do not emulate them inline.

## Interrupted or quarantined control state

If a previous run left an unfinished marker, transaction, or cursor under the
repository's private coordination root, report it; do not delete it, rewrite it,
or run broad git repairs. The parent reconciles evidence first through the
read-only reconcile path in the contract; an interrupted expected-byte
publication keeps its quarantine/previous files as recovery evidence. Never
instruct force pushes, `git clean`, wholesale marker deletion, or reset of
unrelated work. Fresh control writes require the exact expected prior bytes;
changed or foreign bytes block with their evidence preserved.

## Operating contract reference

The complete specified operating contract — fresh/resume forms, required base,
scoped approvals, zero-effect versus charged repair rounds, two CI rounds per
PR, approved deadline extension, preparation/review/publication ordering,
parent-only checkpoints, consumer-owned reproduction, complete-file input
limits, installed-helper setup, conditional nesting and context limits — is
documented in `docs/reference.md` (Autopilot section) and validated offline by
the control modules and journey tests under `scripts/`. The advanced ideas
`autopilot-hard-stage-deadlines` and `autopilot-enforced-writer-isolation` stay
deferred roadmap items and are not implemented here.

## What locks and receipts do not prove

The coordination marker is an ownership, reservation, and transaction record,
not a lock against a malicious privileged writer. Stage envelopes are
correlation records, not security credentials. A matching hash or effect-start
receipt shows that a particular operation recorded a write before proceeding;
it does not prove the write was correct, tested, or unchanged afterward. Plan,
report, Git, and GitHub state remain the authority for execution conclusions;
hashes detect inconsistency and are never claimed as cryptographic proof.
Test entries on a stage result are not execution passes; exceptions are not passes and only `passed` test entries may advance the pipeline.
