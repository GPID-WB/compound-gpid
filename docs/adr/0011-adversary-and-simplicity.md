# ADR 0011: The adversary and the simplicity verifiers: a finding reproduced, three rounds, dropped findings, and `cg.py scope`

Date: 2026-11-27. Status: proposed in task 2.8 (#231) as the working version. It waits for the maintainer's acceptance. Before 2.0 it changes by amending this record.

## Context

The issue asks for four lenses: the adversary (P5), simplicity (P6), the contract verifier (P1, "Spec" in the issue) and claims (P7). This record is about the first two; the second half of task 2.8 adds the other two. For the adversary the issue asks that findings are reproduced, that it is bounded to three rounds, and that dropped findings are listed; for each lens, that it catches its planted violations. Section 4.3 of the plan puts the adversary at the review stage, with bounded rounds for deep work, and the simplicity verifier at the plan and the review stage. The sources the ledger names are addyosmani's `doubt-driven-development` (the work and the contract only, three rounds, doubt theater as a signal code can check) and `code-simplification`, and pstack's `interrogate` (a finding survives only when a run proves it, and what was dropped is reported), with `principle-attack-the-premise` and the principles behind P6.

As in ADR 0009 and ADR 0010, each flag was split in two: the part a rule can find, which code finds with a test, and the part that needs judgement, which the lens names.

Two things were given. The engine (ADR 0008) records each verdict as one more line of the conformance record, with the state of the change it was given on, and opens the pointer of each finding. And a verifier runs a command through `cg.py evidence --run`, whose record keeps the command, cut at 300 characters, its digest, its exit code and a digest of what it printed, and never the output.

## Decision

### The adversary: what "reproduced" means

- **A finding of the adversary stands only on a run of this work that failed.** Its pointer is a record under `.cg-docs/evidence/<work report>/` of a run for this work report, through `evidence --run`, a check of the plan or `repro`, whose exit code is not 0 and that holds its command whole: the digest of the command it keeps is the digest the record holds, so nothing was cut, and anyone can run it again from the record. The sentence of the finding names the line of code where the fault is. A line alone is no proof for the adversary: it shows where a fault would be, not that it happens. P5 said so already: report a finding only when a run proves it, and point at the record of that run.
- **What code holds, and what it cannot.** Code checks the record, its work report, its exit code and that its command is whole. It cannot tell that the probe failed because of the fault and not because of a typo or a missing package, or that the command needs nothing the record does not hold, such as a file in a scratch folder that is gone. The lens asks for a probe of one command, 300 characters at most, that asserts what the requirement asks and builds its inputs in the command. The human reads the command in the record.
- **A key of the principle file, and no verifier named in code.** P5's frontmatter says `proof: run`. `conformance` reads it with the principle, as it reads `stages`, so a lens of a pack that serves P5 is held the same way. A finding of any other verifier is proven as before.
- **Considered and set aside.** Code reruns each probe at `conformance`, as interrogate has the agent that started the adversaries do: the probe's scratch files are gone by then (rule 7 of `verifier.md`), a probe that then fails for that reason would look reproduced, and `conformance` would run commands. Two runs of the same command that both fail: twice the cost, and a typo fails twice too. A line as proof, as for the other verifiers: P5 rules it out.

### The rounds

- **A round is the adversary's verdict on one state of the change.** A verdict on the same state as the adversary's newest one is the same round, and the newer verdict counts. A verdict on a new state is the next round. Code writes `round` into the line, and the listing shows "round 2 of 3". So a round follows the source's cycle: the change moves between rounds, and a fresh adversary on a change that did not move gives no new round. One kickoff is one round; the adversary counts nothing itself.
- **Three at most, and doubt theater stops it.** P5's frontmatter says `rounds: 3`. `conformance` refuses the verdict of a fourth round, and of a third when the last two rounds each gave findings and reproduced none, which code records as `UNVERIFIED`. That is doubt theater as P5 and the source name it, in what code can see. A refused verdict is not recorded, and the message says that the findings go to the human.
- **Considered and set aside.** Every verdict line a round: a verdict recorded again on the same state, after a mistake in the line, would use one up. Rounds inside one turn of the adversary, which it declares: code cannot see them. Doubt theater as the source words it, findings none of which were acted on: what is acted on is the human's choice at review (task 2.9), so code counts what it can see, findings none of which a run reproduced.

### Dropped findings

- **Listed under `dropped` in the conformance record.** The adversary's verdict block has one more list after `findings` (the lens): each suspicion it probed that a run did not reproduce, with the record of its probe and why. The agent that records the verdict gives each with `--dropped` (the guide). Code adds each finding of the adversary that it does not keep, marked "not reproduced", where another verifier's goes under `unverified`. The listing and the line `recorded:` show them, each cut at 300 characters, as a finding is.
- **Considered and set aside.** The note: one sentence of 300 characters. A count of dropped findings for each adversary, as interrogate reports it: the human sees what was tried only with the list. Only what code drops: a verdict of PASS rests on the adversary's own probes that passed.

### The simplicity verifier: what code holds of P6

| Flag | What code finds (a rule of `cg.py scope`) | What stays by judgement |
|---|---|---|
| A change that only tidies | `reformat`: a file git holds whose change is gone when whitespace is ignored | whether the plan asked for that layout; a tidy that changes more than the layout |
| Code that nothing calls | `no-caller`: a function the change adds that no line of the project's code outside its tests names | an exported function, an entry point, a call by a person who uses the package |
| An abstraction with one caller | `one-caller`: such a function that one line names | whether it only forwards, or gives a name the reader needs |
| An option nobody uses | `unused-argument`: an argument of such a function that its body never names | whether a requirement asks for it |
| A check for a state that cannot occur | nothing | a check on a value the code itself sets, or one the contract fixes |
| A file that no slice lists | nothing more: `guard` holds each slice to its files | a file changed after the last slice |
| Code that can go | nothing | the checks run in a scratch copy with the code taken out and no data file |
| A smaller design | nothing | a package the project loads, a setting or the standard library that does the same |

- **`cg.py scope --report <work report>`** compares the files of the change with the commit the work began on, and leaves out `.cg-docs/`, the outputs of the outputs map and each file a data rule names. It gives the number of files and the lines added and removed, beside the number of files the slices list, or for quick work the files given to `tier`: the size of the diff beside the plan's estimate, as P6 asks. It reads code files and never a data file, and it runs nothing. It records one record of `"kind": "scope"`, with the counts, each finding as its rule, where it shows and its fix, the commit and the state of the change. A finding at that record is proof, as at `repro`'s. Exit code 1 when it names a finding.
- **The work playbook runs it once every slice is done, after `repro` and before the verifiers,** so the simplicity verifier reads its record, as the determinism verifier reads that of `repro`. Nothing is changed for its findings. Quick work runs neither.
- **A function is read from one line:** `def name(...)` in Python, `name <- function(...)` in R, with its arguments on that line. Its body is what is indented below it, with a closing brace at its indent. A call is the name standing as a word in a line of the project's code outside test files and comments. These are shapes, as the other rules are, and the known misses are under "Open".
- **Considered and set aside.** The rules in `repro`'s search: its record is P3's, and `repro` refuses while the outputs are not committed, which would leave P6 with nothing. A line in every kickoff that the simplicity verifier runs itself: one more line that one verifier runs, the shape V18 of the review of task 2.7 found. Python's `ast` module: exact for Python, and nothing for R, the main language of the audience. A rule for a file that no slice lists: `guard` holds it for each slice, and at the close it would name the outputs a run wrote.

### The lenses

`packs/core/cg/lenses/adversary.md` and `packs/core/cg/lenses/simplicity.md`, each within its 60 lines, in the shape of the determinism lens. The adversary's: what code holds of a finding, of the rounds, and of a run of an earlier round that failed, which the verifier accounts for; where to probe, with the cases of P5 for analytical work; how a probe proves a flag; the list of dropped; what to leave alone. The simplicity lens: what code found, with the bullet that the verifier accounts for each finding of code; what to flag at the plan stage; a table of the flags; how to prove and propose; what to leave alone. A test holds each lens to its words, and the simplicity lens to every rule of `SCOPE`.

### The planted cases

- `evals/planted/adversary/`: work on an approved plan, its two slices done and its three checks verified, with four faults that no check catches, because the toy survey holds no household that shows them: a household at the line counted as poor, a missing weight read as 0, a negative welfare taken as it is, and a household whose region has no name left out of the national figure. Each case has a probe that fails on its fault and that the agent never sees. CI runs each through `evidence --run`, holds `conformance` to keeping each finding at its record, and to dropping one at a line, at a run that passed, or at a run whose command the record cut (`tests/core/test_adversary_and_simplicity.py`). A decoy, a group with no weight, is answered as the contract asks, and its probe passes. `run_planted.py --verifier adversary` catches a case only by a finding at a run of the verifier's turn that failed and whose sentence names the line of the fault, and asks that the block lists what was dropped.
- `evals/planted/simplicity/`: `before/` is the project at the commit the work began on, which the runner commits first, and `project/` the project as the work leaves it. Three cases at the plan stage (an option no requirement asks for, a check for a state that cannot occur, a slice that tidies a file the goal does not touch) and five at the review stage, four with a rule of `scope`. CI holds `scope` to each, and to naming nothing the change did not add. The runner gives the lens both stages and runs `scope` as the work playbook does.
- The build agent ran the runner with `--dry-run` only.

### Also built with this task

- Step W of the gate asks for the amendment the agent proposes and says "Yes." to it (gate reruns 21 and 23). Two checks say whether the work needed an amendment and whether each was approved on a plain yes, and the check that the plan is the one the human approved in step H is as strict as before.
- The lead skill of `lang-r` says that a slice that changes roxygen comments or an exported function lists `man/` and `NAMESPACE`, or runs `devtools::document()` in a check and lists the files it writes (gate rerun 23).
- The kickoff says that only the verifier `verification` runs the rerun line (V18 of the review of task 2.7; ADR 0010, "Changes").

## Consequences

- `cg.py` went from 2,763 to 2,871 of its 4,000 lines: about 80 for `scope`, its rules and the reading of a function, about 25 for the proof by a run, the rounds and the dropped findings, and the rest for one helper that `repro`, `scope` and the proof share.
- The close of work on a plan runs one more command, which reads the code of the project and runs nothing.
- A probe of the adversary leaves an ad hoc record among the evidence of the work, which never stands for a check of the plan.

## Open

- Whether code also asks that the sentence of an adversary's finding names a line of code, which the runner asks and `conformance` does not.
- Whether `proof: run` and `rounds:` hold for another verifier: any principle file can now say them.
- The rules of `scope` are shapes. Known misses: a function defined over two lines, in an R Markdown or Quarto file, through `assign()`, or as a method indented under a class; a call through a string, such as `do.call("name")` or `getattr()`; a word in a docstring or a string that counts as a call; an argument read only through `...`, `**kwargs` or `match.arg()`. Known false alarms: a function called from a file of another language or only from `NAMESPACE`, an exported function of an R package, and one called only by its tests.
- Whether quick work runs `scope`.
- A probe in Stata: the lens names `python -B -c` and `Rscript -e`, and a one-line Stata probe was not tried here.
