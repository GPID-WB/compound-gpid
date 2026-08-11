# Copilot issue dispatcher (Stage 3)

Stage 3 of the controlled Copilot issue-implementation pipeline provides a
**manually triggered, single-issue dispatcher**. It takes a GitHub issue number,
reuses the Stage 2 [readiness validator](copilot-readiness.md) as the gate, and
(unless running in dry-run mode) assigns the Copilot coding agent, moves the
issue Project `Status` to `In progress` **only after** a successful assignment,
and leaves an audit comment describing the result.

The dispatcher is deliberately bounded: there is **no** recurring trigger, no
multi-issue selection, no automatic use of merge tools, and no automatic
project-goal or milestone progression. Everything that touches GitHub state is
human-triggered through `workflow_dispatch`.

## When to use

- You have a readiness-validated issue (Project `Status` is `Ready` and the
  Stage 2 contract is complete and valid) that you want to hand to the Copilot
  cloud agent, one issue at a time.
- You want a zero-mutation **dry run** to preview what dispatch would do without
  touching GitHub.

## How to run

The workflow is `.github/workflows/copilot-dispatch.yml`. It is triggered from
the **Actions** tab (workflow `Copilot Issue Dispatch` → *Run workflow*):

| Input | Type | Default | Meaning |
|---|---|---|---|
| `issue_number` | number | (required) | The issue to validate and assign. |
| `dry_run` | boolean | `true` | `true` = validate and report only; `false` = run the live dispatch sequence. |

The workflow only runs trusted code from the **default branch** (checkout pins
`github.event.repository.default_branch`); it never checks out a PR head or any
other untrusted ref.

Equivalent local CLI (for fixture/mock-based inspection only — never assigned a
live issue during this implementation):

```bash
# Dry run (zero mutations), human-readable:
python scripts/issue_dispatch.py --issue 9002 --dry-run

# Dry run, machine-readable:
python scripts/issue_dispatch.py --issue 9002 --dry-run --json

# Live sequence (assign -> Project Status In progress -> audit comment):
python scripts/issue_dispatch.py --issue 9002 --no-dry-run
```

> **Do not run the live workflow against a live issue during the Phase 5
> implementation pass.** Use fixtures and mocks only. Live dispatch requires
> explicit human authorization after review/merge plus the credentials described
> below.

## What the dispatcher guarantees

1. **Dry-run is zero-mutation.** A dry run performs no assignment, Project
   update, comment, label, or any other GitHub mutation.
2. **Fail-closed gate.** Before any non-dry-run mutation the dispatcher:
   - validates readiness (reuses the Stage 2 validator, no logic is
     reproduced);
   - performs all duplicate/idempotency checks;
   - revalidates readiness immediately before assignment;
   - fails closed if either validation fails or the GitHub state changed
     between the two validations.
3. **Fixed mutation order.**
   1. assign only `copilot-swe-agent[bot]`;
   2. only **after** assignment succeeds, set the issue Project `Status` to
      `In progress`;
   3. add an audit comment describing the result.
4. **`In progress` is never set before a successful assignment.**
5. **Assignment succeeds but Project update fails**: the dispatcher does not
   unassign Copilot automatically, does not speculate about a rollback, leaves
   an observable failure comment, exits non-zero, and reports the manual
   recovery procedure.
6. **Idempotent no-op.** A repeat dispatch for an already-assigned issue or for
   an issue with an existing open implementation PR is a no-op (exit 0) with a
   clear explanation; it never re-assigns.

## Exit codes

The dispatcher extends the readiness exit-code contract:

| Code | Meaning |
|---|---|
| `0` | Ready and dry-run success; dispatched; or idempotent no-op |
| `2` | Validation failure — issue not ready; no mutation (*except* already-dispatched states, which return `0` as an idempotent no-op) |
| `3` | Configuration error (e.g., missing credential, unsupported status) |
| `4` | API/network error |
| `5` | Assignment failed; issue left Ready; failure comment written |
| `6` | Assignment succeeded but Project update failed; assignee kept; recovery comment written |
| `7` | Readiness changed between validation and assignment; failed closed |

## JSON result

The workflow always passes `--json`, so the dispatcher emits one object:

```json
{
  "issue": 9002,
  "outcome": "dispatched",
  "dryRun": false,
  "exitCode": 0,
  "exitReason": "ready",
  "mutations": ["assign:copilot-swe-agent[bot]", "project:In progress", "comment:dispatched"],
  "messages": ["Dispatched to copilot-swe-agent[bot]; Project Status set to 'In progress'."]
}
```

`exitReason` values: `ready`, `validation_failure`, `config_error`, `api_error`,
`assign_failed`, `project_update_failed`, `state_changed_before_assignment`.
The `mutations` array is the ordered audit log every path must populate (a
`comment:failed` entry records a failed audit-comment write).

## Credentials and isolation

The workflow uses **two separate least-privilege credentials** (created in
repository settings, never by the workflow, never combined into one token):

| Environment variable | Used for | Required access |
|---|---|---|
| `COPILOT_ASSIGN_TOKEN` | assignment + audit comments | issues write |
| `PROJECT_SYNC_TOKEN` | Project `Status` mutation | project write |

Isolation rules enforced and tested:

- Neither credential is referenced by any `pull_request` or
  `pull_request_target` workflow that executes untrusted code.
- The dispatcher fails closed (exit `3`, `config_error`) when a required
  credential is not configured.
- Issue content is treated as untrusted input; request bodies are written to
  temp files and passed through `gh --input` / `--body-file` (argv-safe and
  path-safe); issue content never reaches a shell string.

### Deployment-specific Project IDs

The Project-node, Status-field, and Status-option IDs are the deployed
`CompoundGPID-progress` project's verified constants (Stage 0A, 2026-08-06) and
are pinned in `scripts/issues/dispatch_client.py`. They are **not** secrets. If
that project is ever recreated or the pipeline is run against a different org
project, update these constants (or lift them into environment-provided
settings) before using the dispatcher.

## Manual recovery procedure

If assignment succeeds but the Project update fails (exit `6`):

- **Do not unassign Copilot automatically.**
- Inspect the `PROJECT_SYNC_TOKEN` scope and the issue's Project item, then set
  the Project `Status` to `In progress` manually (or re-run dispatch after
  correcting the credential).
- Do not re-assign Copilot while the assignee is still present.

## Relation to other stages

- Stage 2 ([readiness validator](copilot-readiness.md)) is the gate; the
  dispatcher reuses it and never reproduces its rules.
- Stage 4 (Project reconciliation) and later stages are **not** implemented by
  the dispatcher.
- This page documents inputs, dry-run, permissions, and recovery per the plan's
  documentation checklist.

## Testing

Deterministic tests live in `scripts/tests/test_issue_dispatch.py` and use
inline fixtures, fake read clients, fake mutation clients, and stub `gh`
runners. No test contacts live GitHub. Coverage includes dry-run zero-mutation,
initial readiness failure, readiness changing before the second validation,
assignment failure, Project-update failure after a successful assignment,
mutation ordering, audit-comment ordering, idempotent no-op, exact Copilot bot
identity, and the workflow's trigger/concurrency/permissions/checkout/secret
constraints.

```bash
python -m pytest scripts/tests/test_issue_dispatch.py -q
```

The test is registered in the required `Native target Python gate` pytest list
in `.github/workflows/tests.yml`.
