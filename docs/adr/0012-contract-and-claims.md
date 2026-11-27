# ADR 0012: The contract and the claims verifiers: what code holds of P1 and P7, `cg.py claims`, and the two points of the first lens run

Date: 2026-11-27. Status: proposed in task 2.8 (#231), its second half, as the working version. It waits for the maintainer's acceptance. Before 2.0 it changes by amending this record.

## Context

The issue asks for four lenses. ADR 0011 is about the adversary and the simplicity verifiers; this record is about the contract verifier (P1, "Spec" in the issue) and the claims verifier (P7), each of which must catch its planted violations. Section 4.3 of the plan puts the contract verifier at the plan stage and, as "Spec fidelity", at the review stage, and the claims verifier at the review stage. The sources the ledger names were read in full at their pinned commits: addyosmani's `spec-driven-development` (success criteria that are specific and can be tested, and anything the requirements do not name is out), `using-agent-skills` (surface assumptions, push back, verify and never assume, touch only what was asked) and `source-driven-development` (cite the page, and call unverified what was not found); mattpocock's `grilling` and `to-spec`; pstack's `blast-radius` (a writeup that sounds right is worth nothing, a ladder of certainty from "you said so" to "you ran it", and never a caller or an API made up) and `poteto-mode` (each claim with its evidence or a label: measured, inferred or guess); and principles 1 and 6 of `docs/philosophy.md`.

The first run of the verification lens (`.cg-docs/gate-m1/lens-verification-1/`) gave two points to this task: a number that measures something else, which the lens's question did not turn into a finding, and a claim of validation that names no record, which `unrecorded` does not find because it names no check.

As in ADR 0009 to 0011, each flag was split in two: the part a rule can find, which code finds with a test, and the part that needs judgement, which the lens names.

Three things were given. `cg.py validate` already holds what P1 asks of a plan's contract, and the plan playbook runs it before the verifiers. The kickoff already says whether the human approved the plan as it now reads, and `evidence` runs no check of a plan that changed since. The work report's template has a Changed table and an Evidence section, where the agent's claims are written.

## Decision

### What code holds of P1

| Flag | What code finds | What stays by judgement |
|---|---|---|
| No statement of what a wrong result looks like | `validate`: the intent has "A wrong result", and `new plan` takes only a decided intent (as before) | whether a check fails on that wrong result |
| A requirement with no check, or a check that serves none | `validate`: each requirement has a check, and each check names a requirement the table holds (as before) | a check that would pass with its requirement broken |
| A check that cannot fail, or a pass condition that is a matter of opinion | `validate`: each check has an outcome, and none that says it cannot fail (as before); at the review stage, `cannot-fail` of the rerun (P4) | an outcome that is a matter of opinion |
| The plan changed with no amendment | the kickoff's line "The contract", and `evidence`, which runs no check of a plan changed since its yes (as before) | none |
| Something the contract names that was not built | `not-built` of `cg.py claims`: a file the approved plan names in its Goal, Requirements, Checks (its commands left out), data register or slices that the project does not hold when the work is done | a requirement built otherwise: another value, a group left out |
| Something built that the contract does not name | nothing more: `guard` holds each slice to its files | an output, a measure or an option that no requirement asks for, or that Out of scope names |

- **At the plan stage, code's part is `validate`.** The plan playbook runs it before the verifiers and goes on only with no problem and no warning, so the contract verifier judges a plan that code has passed: what its words say, against the intent. Considered and set aside: a new rule at the plan stage, such as `cannot-fail` on the commands or a list of words of opinion in "Fails when". A warning of `validate` stops step 6 of the plan playbook, so either rule is a new refusal of what `approve` takes, which decision 7 of task 2.7 left with the maintainer and which every gate's plan would meet.

### What code holds of P7

| Flag | What code finds (a rule of `cg.py claims`) | What stays by judgement |
|---|---|---|
| A claim with no label | nothing: the template of the work report asks for no label | which of measured, inferred or guess the line is |
| A claim labelled measured with no pointer | `unpointed`: a line labelled measured, at its start, in brackets or as a cell, that names no check, no file and no record | none |
| A pointer that does not show what is claimed | `no-such-file`: a file or a record that the work report names in backticks, or with a line in prose, and that the project does not hold; a line past the end of its file; a record that is not of this work | whether what the pointer opens shows what the line says |
| An inference or a guess written as fact | nothing | a cause, a trend or a comparison that nothing shows |
| A function, argument, package, citation or file named that does not exist | `no-such-file` for a file; `undefined`: a function named in backticks, `name()`, that no R or Python code of the project defines on one line, as `scope` reads a definition, and that is no built-in function of Python | a function of R or of a package the project loads, which its documentation names |
| A number in the text that differs from the number in the output file | `unmatched`: a number with a decimal point or a percent sign, on a line that names an output of the outputs map in backticks, that the output does not hold at the number's decimals, or times 100 for a percent | whether the number is a result, and not a line, a tolerance or a count |
| A file the Changed table names that did not change | `unchanged`: a row whose file the change left as the commit the work began on holds it | none |

- **Which lines are claims.** The lines of the work report that the agent wrote (`said`): none of its frontmatter, none that the template holds as it stands, none under "## Asked", which holds the human's words that P7 leaves alone, and no heading, no header or rule of a table, no fenced code and no comment. The rerun reads the same lines for `unrecorded` and `unbacked`, which until now read every line, the human's request and the template's text included.

### `cg.py claims`

- **What it reads and keeps.** `cg.py claims --report <work report>` reads the work report, the plan it names, the names of the files of the project, the records of this work, the outputs of the outputs map, and the R and Python code of the project. It reads no file that a data rule names and none of a megabyte or more, and it runs nothing. It records one record of `"kind": "claims"`: each finding as its rule, the line of the work report or of the plan where it shows, and the change that would replace it; the commit and the state of the change. It never keeps or shows a number of the report or of an output, or what a line holds (P12). A finding at its record is proof, as at the records of `repro`, the rerun and `scope`. Exit code 1 when it names a finding.
- **One command for both principles.** P1's part at the review stage is one rule, a file the plan names that is not there, and P7's `no-such-file` is the same test on the work report: one reading of the names and of the project serves both. The record holds the rules of both, and each lens names its own and leaves the other's. Considered and set aside: a command for each, which is one more line in the work playbook, at 118 of its 120 lines, and a second reading of the same files; `not-built` in `scope`, whose record is P6's and which reads no text of the plan; the rules in the rerun, which only the verification verifier runs, so a claims verifier started at the same moment would often find no record; and a line in every kickoff that one verifier runs, the shape V18 of the review of task 2.7 found.
- **Who runs it.** The work playbook, after `scope` and before the verifiers. The playbook now has the agent fill every section of the work report but its status before `scope` and `claims`, where it said to fill them after the verifiers: the claims verifier read a work report that the agent had not finished, and `claims` would too. This moves one sentence that earlier gates passed. Quick work runs neither command.

### A claim of validation that names no record (point 2 of the lens run)

- **The rule is the verification verifier's: `unbacked`, a rule of the rerun beside `unrecorded`.** A claim of success or of validation, a word such as verified, validated, passes, confirmed, matches, agrees or reproduces with no negation in the three words before it, on a line that names no check of the plan and no record of a run of this work. `unrecorded` and `unbacked` share one pattern, `CLAIM`, which now holds the words of validation too, and differ in what the line names.
- **Why P4 and not P7.** Section 4.3 of the approved plan gives the verification verifier "flags claims with no evidence", and task 2.7 held that line with `unrecorded`. The claim is one of validation, which is the other half of P4, and its fix is a check that compares the number with its source, which only P4's verifier asks for. P7's verifier holds a claim's label and its pointer: `unpointed` and `no-such-file`. So the planted case stays in `evals/planted/verification/`, with `code` now `unbacked`, the claims project plants none like it, and no case is expected of two verifiers. The claims lens has its verifier leave `unrecorded` and `unbacked`. Considered and set aside: the rule in `cg.py claims`, with the case moved to the claims project. The verifier that missed it in the lens run would then not see it, and the claims verifier would hold a claim to its evidence, which the plan gives to P4.

### Every number traced (point 1 of the lens run)

The verification lens has the verifier trace each number the work reports from the line that writes it to the line that computes it and on to the line that reads its input, and name each filter, merge, weight and unit on the way. A finding points at that filter, merge, weight or unit, and says what the number measures there. No rule of code: what a number measures is judgement. Considered and set aside: a rule that names each condition on a weight, such as `if row["weight"]`, which would also name every input assertion that P10 asks for.

### The lens run, read again

The runner matches findings and cases one to one, and a finding caught a case within three lines of its line, or at a place under "or". In the lens run Codex flagged the filter on the weight at its line, `pipeline.py:12`, and Kilo the claim of validation at its line. Each had folded the two cases of C5, a check never run and a claim that it passes, into one finding, and the matching gave the finding at the right line to the case beside it: C4's "or" holds `pipeline.py`, and the claim on C5 stands one line above the claim of validation. So the counts, 7 and 6 of 9, were right, and the cases named as missed were not: Codex missed the claim of validation, which only its note names, and Kilo the filter. Both points stand. A finding at the line of a case now catches that case alone (`judge` in the runner), and the README of the lens run has a dated note.

### The lenses

`packs/core/cg/lenses/contract.md`, 52 lines: what code holds at each stage (`validate` at the plan stage, `not-built` of `claims` at the review stage, the kickoff's line on the contract); what to flag at the plan stage, against the intent; the table of the flags; how to prove and propose; what to leave alone. `packs/core/cg/lenses/claims.md`, 51 lines: what code found; each claim as measured, inferred or guess, from `poteto-mode`'s rule for a reply and `blast-radius`'s ladder; the table; how to prove and propose; what to leave alone. Each has the bullet that the verifier accounts for each finding of code. A test holds each lens to its words, its 60 lines and every rule of its principle.

### The planted cases

- `evals/planted/contract/`: an intent and the plan the human approved on it, with three cases at the plan stage, each by judgement in a plan that `validate` passes: a check that names its requirement and passes with it broken, a "Fails when" that is a matter of opinion, and the intent's wrong result with no check that fails on it. At the review stage four: a note the plan says the work writes and that it never wrote (`not-built`); a poverty line of 3.65 where the contract says 3.0; the regions of fewer than three households left out of the table, where the contract and the intent ask for every region; and a poverty gap, which Out of scope names.
- `evals/planted/claims/`: `before/`, which the runner commits first, then the work, and a work report with eight claims. Five have a rule of `claims`: a record that is not there, 0.52 where the output holds another number, a claim labelled measured with no pointer, a function the project does not define, and a row of the Changed table for a file the change left as it was. Three are by judgement: a cause written as fact from a share, a claim that the check it names does not show, and "Nothing" under "Not checked" where the plan names what no check would catch.
- CI holds code's part, in `tests/core/test_contract_and_claims.py`: each case with a rule is found at its line, and every finding is a planted case, so a claim the work report makes rightly is none. `run_planted.py --verifier contract` and `--verifier claims` give each lens its project; the build agent ran them with `--dry-run` only.

## Consequences

- `cg.py` went from 2,871 to 2,979 of its 4,000 lines: about 77 for `claims`, its table and how it reads a name; about 22 for the lines of the work report that hold a claim (`said`), which the rerun shares, and for `unbacked`; and the rest for the parser and the usage. The reading of the code is one helper that `scope` now shares.
- The close of work on a plan runs one more command, which reads and runs nothing.
- The work report is filled before the verifiers start, not after them.

## Open

- Whether the template of the work report asks for a label on each claim of its Evidence section. Until it does, a claim with no label is judgement, and a rule for it would name nearly every line of every work report.
- The rules are shapes. Known misses: a file named in prose with no line; a function whose name holds a dot or `::`, or that is defined over two lines or in R Markdown; a number with a thousands separator or in words; an output named in prose. Known false alarms: a function of base R named in backticks (`undefined`, to judge); a name in backticks with a suffix that is no file of the project, such as `cg.py` alone; a file the plan names that the work is not meant to build, such as one it reads from another folder.
- Whether code applies a rule to the plan's commands or its "Fails when" at the plan stage: the maintainer's, with decision 7 of task 2.7.
- Whether quick work runs `claims`, as it runs neither `repro` nor `scope`.
- P7 inspects any text written for readers, and `claims` reads the work report alone.
