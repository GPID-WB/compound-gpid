# Copilot issue readiness validator

Stage 2 of the controlled Copilot issue-implementation pipeline provides a
**deterministic, read-only validator** that decides whether a GitHub issue is
ready to be dispatched to the Copilot coding agent. It does **not** dispatch,
assign, comment, label, or change any Project status. Passing validation only
means the issue is *eligible* — a human (or a later Stage 3 dispatcher) still
has to act.

The readiness contract is the structured Markdown issue body proven by the
Stage 1 pilot (issue #127). This page documents the canonical contract, how to
run the validator, its JSON result and exit codes, and the difference between
validation and dispatch.

## Canonical readiness contract

The contract is a GitHub issue body written in Markdown. Section headings are
matched **exactly** (case-sensitive, `## ` level); fenced code blocks are
ignored when locating sections, the tracked marker, and the feature id, so
examples written inside ` ``` ` fences are never mistaken for real contract
data. The issue body is treated as **untrusted data** throughout. Fences are
expected to be balanced within each section: a fence opened in one section and
closed in a later one (or left unclosed) is not part of the proven contract and
may be parsed more permissively.

A ready issue must contain all of the following, in any order:

### Tracked feature marker

A hidden HTML comment as the first marker in the body:

```
<!-- compound-gpid-tracked: <feature-id> -->
```

`<feature-id>` is lowercase kebab-case (`^[a-z0-9][a-z0-9-]*$`), for example
`artifact-html-opt-in-default`. This is the recovery/duplicate-detection
identifier; it is not canonical linkage by itself.

### Required `##` sections

| Section heading (exact) | Requirement |
|---|---|
| `## Roadmap linkage` | Non-empty. The body must contain **exactly one** `**Feature ID:** \`<id>\`` line overall (the Feature ID is matched body-wide, not scoped to this section); the id must match the tracked marker. |
| `## Ready for Copilot` | At least one checklist item, and every item is checked (`- [x]`). This is the explicit human readiness confirmation. |
| `## Outcome` | Non-empty. The intended outcome. |
| `## Acceptance criteria` | Non-empty. Objective, command-checkable criteria. |
| `## Scope` | Non-empty. The implementation scope. |
| `## Non-goals` | Non-empty. |
| `## Expected allowed paths` | At least one path entry. Each entry is a backtick code span on a list item. |
| `## Prohibited paths` | At least one path entry (same format). |
| `## Verification commands` | Non-empty: at least one fenced code block containing commands. |
| `## Dependencies / blockers` | Deterministic dependency handling (see below). |
| `## Risk class` | Contains `low`, `medium`, or `high`. |
| `## Human review instructions` | Non-empty. |
| `## Blocked-stop conditions` | Non-empty. |

Other sections (for example `## Summary`, `## Why`, `## Implementation
guidance`, `## Required tests`) are allowed but not required.

### Path entries

Path entries are the backtick code spans on `- ` (or `* `) list items inside
`## Expected allowed paths` and `## Prohibited paths`. List items without a code
span are treated as prose and ignored, so a section may mix path entries with
descriptive bullets.

A path entry is rejected if it is:

- empty or contains a null byte;
- absolute (`/abs`), a Windows drive (`C:\` or `C:/`), or UNC (`\\server` / `//server`);
- contains a backslash (git pathspecs use forward slashes only);
- contains a `..` traversal segment;
- has an empty segment (consecutive or trailing slash);
- has unbalanced glob brackets (`[a-z` without a closing `]`).

Valid examples: `` `docs/example.md` ``, `` `scripts/**/*.py` ``,
`` `.github/workflows/**` ``, `` `a/b/[0-9].md` ``.

### Dependencies / blockers

The section is parsed line by line. The issue is **blocked** (validation
fails) when the section contains an unchecked checklist item (`- [ ]`) or a
`blocked by` phrase not explicitly negated (for example "not blocked by",
"cannot be blocked by", "can't be blocked by"). A section that says `None`,
lists only resolved items (`- [x]`), or contains only informational prose is
not blocking.

### Risk class

A line whose content is exactly `low`, `medium`, or `high` (optionally wrapped
in backticks) is the risk class; prose such as "low confidence" is rejected.
Anything else (for example `critical`) fails validation.

## How to run the validator

The validator is a stdlib-only Python tool. Run it from the repository root:

```bash
# Live issue (read-only GitHub access via the gh CLI):
python scripts/issue_readiness.py --issue 127 --dry-run

# Machine-readable JSON:
python scripts/issue_readiness.py --issue 127 --dry-run --json

# Offline fixture (no network; used for testing and dry-run evidence):
python scripts/issue_readiness.py --fixture scripts/tests/fixtures/ready_issue.json --dry-run --json
```

`--dry-run` is the canonical and only mode. The validator **never mutates**
GitHub state, so `--dry-run` is always on; the flag is accepted for interface
consistency with the future Stage 3 dispatcher.

`--issue` and `--fixture` are mutually exclusive and one is required:

- `--issue N` fetches the issue body, open pull requests, assignees, and
  Project Status through the `gh` CLI (argv-safe; the untrusted body is never
  interpolated into a shell string).
- `--fixture PATH` reads a local JSON fixture that supplies the issue body and
  the mocked GitHub state, so the validator can run fully offline. The fixture
  may reference a separate body file via `"bodyFile"`. PR items under
  `"openClosingPRs"` use the same JSON keys as `gh pr list` (e.g.,
  `headRefName`, author as `{ "login": ... }`).

Project Status is read via the Projects v2 GraphQL API, which requires the
`read:project` scope. If that scope is missing, the validator reports a
configuration error (exit 3) rather than guessing.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | **Ready** — every rule passed. |
| `2` | **Not ready** — at least one validation rule failed (contract or GitHub state). |
| `3` | **Configuration error** — cannot complete validation (gh missing, issue not found, missing `read:project` scope, bad arguments). |
| `4` | **API/network error** — cannot complete validation (GitHub 5xx, timeout, rate limit, malformed response). |

Exit codes deliberately distinguish a *validation* failure (the issue is
reachable but not ready, exit 2) from an *inability to complete* (configuration
or API/network, exit 3 or 4).

## Rules

The validator reports each rule with a stable identifier. Contract rules run
on the parsed body only; state rules run on the live (or fixture) GitHub state.

| ID | Name | Scope |
|---|---|---|
| R001 | `marker-present` | contract |
| R002 | `feature-id-declared` | contract |
| R003 | `feature-id-marker-match` | contract |
| R004 | `required-sections-present` | contract |
| R005 | `no-duplicate-sections` | contract |
| R006 | `readiness-confirmation-checked` | contract |
| R007 | `acceptance-criteria-nonempty` | contract |
| R008 | `verification-commands-nonempty` | contract |
| R009 | `risk-class-valid` | contract |
| R010 | `allowed-paths-present` | contract |
| R011 | `prohibited-paths-present` | contract |
| R012 | `path-entries-safe` | contract |
| R013 | `blocked-stop-conditions-nonempty` | contract |
| R014 | `dependencies-not-blocking` | contract |
| R015 | `outcome-nonempty` | contract |
| R016 | `scope-nonempty` | contract |
| R017 | `non-goals-nonempty` | contract |
| R018 | `human-review-instructions-nonempty` | contract |
| R019 | `project-status-ready` | state |
| R020 | `no-open-closing-pr` | state |
| R021 | `copilot-not-assigned` | state |

A result is **ready** only when every rule passes.

`R020` (`no-open-closing-pr`) detects closing PRs by scanning open pull requests
for a closing keyword (`closes #N`, etc.) in the PR body. Detection is
body-keyword-only: a PR that closes the issue via the GitHub linking UI without
such a phrase in its body is not counted. The scan pages through open PRs
(`--page N`, 100 per page) and terminates as soon as a page is shorter than the
page size.

## JSON result

With `--json`, the validator writes a single JSON object to stdout:

```json
{
  "issue": 127,
  "ready": false,
  "dryRun": true,
  "exitCode": 2,
  "exitReason": "validation_failure",
  "summary": "NOT READY — 2 rule(s) failed",
  "rules": [
    { "id": "R001", "name": "marker-present", "passed": true, "detail": "..." }
  ],
  "failedRules": [
    { "id": "R019", "name": "project-status-ready", "detail": "Project Status is 'Backlog', expected 'Ready'" }
  ],
  "state": {
    "issueState": "OPEN",
    "projectStatus": "Backlog",
    "openClosingPRs": [],
    "copilotAssigned": false,
    "assignees": ["randrescastaneda"]
  },
  "errors": []
}
```

When the validator cannot complete (exit 3 or 4), `rules` and `state` are empty
and `errors` describes the failure:

```json
{
  "issue": 127,
  "ready": false,
  "dryRun": true,
  "exitCode": 3,
  "exitReason": "config_error",
  "summary": "CANNOT COMPLETE — config_error",
  "rules": [],
  "failedRules": [],
  "state": {},
  "errors": [{ "type": "config_error", "message": "GitHub authorization/scope error: ..." }]
}
```

## Validation vs. dispatch

The validator only **checks** readiness. It performs no GitHub mutation of any
kind:

- it does not assign Copilot;
- it does not change the Project `Status` field;
- it does not create, edit, close, label, or comment on issues or pull requests;
- it does not write to `roadmap.json`.

Dispatch (assigning Copilot and moving the issue to `In progress`) is a
separate, later stage (Stage 3) that is **not** implemented here. The
dispatcher will re-run this validator immediately before assigning, and only
assigns when the result is ready. A passing validator result is a necessary,
not a sufficient, condition for dispatch — a human still reviews and approves
the actual assignment.

**A passing result does not assign Copilot or change Project status.**

## Testing

Deterministic tests live in `scripts/tests/test_issue_readiness.py` (~127
tests) and use inline fixtures plus mocked GitHub responses; no test depends on
live GitHub state. The test is registered in the required `Native target Python
gate` pytest list in `.github/workflows/tests.yml`, which pins Python 3.11, so it
runs as part of a required CI check on both `windows-2022` and `macos-14`.

```bash
python -m pytest scripts/tests/test_issue_readiness.py -q
```

Offline fixtures for dry-run evidence live in `scripts/tests/fixtures/`.