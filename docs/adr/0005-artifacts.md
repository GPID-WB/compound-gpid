# ADR 0005: The artifact schema, approvals and the tier

Date: 2026-11-25. Status: proposed in task 2.1 (#224) as the working version. It waits for the review by Opus 5.5 and for the maintainer's acceptance. Before 2.0 it changes by amending this record. Amended the same day with the maintainer's decision on who answers for the data (under Tier).

## Context

Artifacts carry the work between phases and between sessions. In version 1 nothing checked them: plans alone used thirty frontmatter keys, some with nested blocks, and a status was whatever the agent typed. A version 1 folder still has to be readable as it is. This repository's own has 668 artifacts.

The first gate (#223) also showed three things an agent gets wrong when they are left to its reading of a playbook: whether a record is complete, whether the human approved the plan as it now reads, and how risky a change is. Principle P3 puts each of them in code.

## Decision

### Schema 2

- **The marker is `schema: 2` in the frontmatter.** A file with no `schema` key is version 1. It is read as it is, in subfolders too, and it is never failed and never converted. Its type is its folder's, and its status is read through one table of version 1 statuses. A higher number than 2 is an error that asks for a newer core.
- **Frontmatter is flat.** One `key: value` line per key. A value is text or a one-line list such as `[a, b]`.
- **The schema is one table in `cg.py`, `ARTIFACTS`.** For each type it gives the folder, the statuses with what each means for status (waiting on the human, open, closed), and the headings the body must hold. The folders are version 1's, so old and new artifacts sit together. `templates/` holds one template per type, and a test holds each template to the schema.
- **Keys.** Every artifact has `type`, `schema`, `title`, `date` and `status`. A link to another artifact is a path from the project root under `intent`, `plan`, `work-report`, `review` or `supersedes`, and it must resolve. `size`, `decided-by` and `tags` are the other keys. Any other key is a warning.
- **A plan's contract carries IDs** (P1, and version 1 issue #66). Requirements are `R1`, `R2` and so on; checks are `C1`, `C2` and so on. Every requirement has a check that names it. Every check names a requirement that exists, a command, and the outcome that means failure.
- **Unfilled template text.** A line that is still the template's own request to fill a part in is a warning while the artifact has its first status, the one `new` writes. After that it is an error, so a work report cannot be `completed` with a part left unfilled.
- **`cg.py validate`** fails on errors. With `--strict`, for a project's CI, it fails on warnings too, so nothing half-written is merged.

### Approvals

- **One approval is one file**, `.cg-docs/approvals/<plan file name>.<start of the digest>.json`. It holds the plan's path, the digest, the human's reply word for word, the name and email from git's configuration, and the time.
- **The digest covers the plan's body, below the frontmatter.** Line ends and trailing spaces are left out, so a sync or an editor cannot void an approval. Considered and set aside: the whole file, because a status change would void the approval; and the Contract section alone, because the slices and the data register could then change with no new approval.
- **An approved plan is frozen.** Progress goes in the work report. A change to the plan is an amendment: the text changes, the human approves again, a second record is written, and the first one stays.
- **Code moves the status from `draft` to `approved`.** A status typed into the file is not an approval: `validate` fails a plan whose status is `approved`, `in-progress` or `completed` with no record for its text, and `status` lists it under `waiting-on-human`.
- **`cg.py approve` refuses** a plan that fails the schema or still holds template text, an empty reply, and the three replies P2 names as not a yes. Whether any other reply is a clear yes is by judgement, for the `ownership` verifier.
- A plan takes an approval, and so does the human's decision on data (under Tier). Sign-off (task 2.10) can use the same record.

### Tier

- **Two levels: `low` and `elevated`.** One yes makes the tier elevated, and elevated is a hard stop in quick work. A third level waits for an observed need.
- **Six facts are declared**, each yes or no, and `cg.py tier` refuses to answer until all six are: `number` (an estimate, a weight, a published output), `personal`, `irreversible` (a deletion), `interface` (a dependency, a schema), `choice` and `no-check`. The quick playbook defines each.
- **Two facts are computed.** `size`: the change touches more than five files. `data`: a data file the work reads is not cleared for this coding agent. A file is cleared when the rule recorded for it, or for the nearest folder above it, gives `Public`, or a level that `approved-tools` lets this coding agent read, ranked by `classification-levels`. A file with no rule is not cleared.
- **The human answers for the data** (the maintainer's decision, 2026-11-25). Code records what the human declares and does not judge it: a file declared `Public` is cleared. The human may also decide that a coding agent reads a file that is not cleared. The agent warns them first, and `cg.py approve --reads <file or folder> --agent <name> --reply "..."` records the decision as one file, `.cg-docs/approvals/data.<digest>.json`: the place, the coding agent, the level the file had, the reply word for word, the name and email from git, and the time. From then on `tier` names the decision on its `data` line on every run and does not raise the tier for that file, and `status` lists it under `data-decisions`. The file still counts as not cleared.
- **A decision on data holds for one coding agent, one place and one level.** A folder covers what is under it. When the file's level changes, the decision no longer covers it and the work stops for a new one. Considered and set aside: a key in `config.json`, because that file holds what the organization allows and a later `setup` run rewrites it; and a command of its own, because `approve` already checks the reply and the identity.

## Consequences

- A version 1 folder needs no migration step, and task 7.1 has no artifacts to convert.
- Later playbooks get their gates from code: the plan playbook (2.3) ends in `approve`, and work (2.4) can refuse to start on a plan that `validate` fails.
- `cg.py` is at 1,332 of its 2,500 lines, with ten commands of milestone 2 still to come.
- An agent can now read data its organization has not approved it for, when the human says so. The record names who decided, and the `governance` verifier leaves that decision to the human (P12, "Leave alone").

## Open

- Closed on 2026-11-25: P12's check line said the tier is raised for any dataset above Public or unclassified, and the code raised it only for a file not cleared for this coding agent. The maintainer decided that the line changes. P12 now says what `tier` does.
- A decision on data is recorded in quick work only. The plan playbook (2.3) has to say how the data register and these decisions meet.
- The statuses and headings of the intent, the review, the decision record and the solution are the smallest set their principles name. The tasks that write their playbooks (2.2, 2.9, 2.11, 2.13) may add to them.
- In quick work the human's yes to the short contract at an elevated tier is still text in the work report, and the agent copies the lines of `tier` into it. Tasks 2.3 and 2.4 decide whether code records them.
