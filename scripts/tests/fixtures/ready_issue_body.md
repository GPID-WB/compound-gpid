<!-- compound-gpid-tracked: example-ready-issue -->

## Summary

Example implementation-ready issue used as a non-production fixture for the
readiness validator dry-run. It mirrors the structured Markdown contract proven
by the Stage 1 pilot (issue #127).

## Roadmap linkage

- **Feature ID:** `example-ready-issue`
- **Roadmap milestone:** `workflow-maturity`
- **Canonical linkage:** synthetic fixture, not linked to a live roadmap feature

## Ready for Copilot

- [x] Human has reviewed and approved this execution contract
- [x] Roadmap feature has been created and linked to this issue
- [x] Exact allowed-path closure has been confirmed
- [x] Project Status has been changed from `Backlog` to `Ready`

Do not assign Copilot until all four boxes are checked.

## Outcome

The example behavior is implemented and objectively verified with existing
repository commands.

## Acceptance criteria

- [ ] The example module produces the expected output
- [ ] The focused test suite passes
- [ ] No files outside the allowed paths are modified

## Scope

Included:

- update one example module
- update the focused tests

## Non-goals

- no GitHub Actions workflow changes
- no new dependencies
- no changes to the Pester runner

## Expected allowed paths

- `docs/example.md`
- `scripts/example.py`
- `scripts/tests/test_example.py`

## Prohibited paths

- `.github/workflows/**`
- `roadmap.json`
- `tests/Run-Tests.ps1`
- `bin/**`

## Verification commands

```bash
python -m pytest scripts/tests/test_example.py -q
```

## Dependencies / blockers

None currently known.

## Risk class

`low`

## Human review instructions

- Confirm the diff touches only allowed paths
- Confirm every acceptance criterion is objectively met
- Merge manually; do not bypass required checks

## Blocked-stop conditions

- Copilot edits any prohibited path
- Required CI is red after fix attempts are exhausted
- A change outside the allowed paths is required to complete the task