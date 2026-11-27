---
name: adversary
principle: P5
derived-from: "addyosmani/agent-skills@e997ac5:skills/doubt-driven-development/SKILL.md; cursor/plugins@ca782ed:pstack/skills/interrogate/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-attack-the-premise/SKILL.md"
---

# Lens: adversary

This lens is for the verifier of P5. It says what code holds of your findings, where to probe, how a probe proves a flag, and what you list as dropped. It adds to the section "Verifier" of your principle file and takes nothing from it.

## What code holds

A finding of yours stands only when a run reproduced it. Its pointer is the record of a probe you ran through the line your kickoff gives for a run, the probe ended with an exit code other than 0, and the record holds its command whole, so that anyone can run it again. Code lists every other finding as dropped, not reproduced, beside the ones you drop yourself.

- Your kickoff is one round. The work has three rounds at most, one for each state of the change, and code numbers them. It refuses a fourth, and a third after two rounds that gave findings and reproduced none, which is doubt theater.
- The records of the work are in the folder of evidence that your kickoff names. Account for each run in it that ended with an exit code other than 0 and is no check of the plan, such as a probe of an earlier round: run its command again through the line for a run, and write it as a finding when it fails again, or under `dropped` when it passes.
- A check of the plan that fails is P4's, and an output that two runs write differently is P3's: leave both.

## Where to probe

Read the contract first: the goal, each requirement, what a wrong result looks like in the intent the plan is built on, and the line of the plan on what no check would catch. Ask what would make the work break each requirement, and probe the cases the author is least likely to have run:

- a value at a boundary: welfare at the line, a share of 0 or 1, the first and the last period;
- what is missing or zero: a missing weight or welfare, a weight of 0, an empty group, one row;
- what is there twice or not at all: a duplicated identifier, a key that a merge does not match, or matches twice;
- what changes the meaning of a number: another currency, PPP vintage, unit or sign, a negative or zero welfare;
- a premise that two failed fixes share: write it down and test it first.

## Prove with a probe

- A probe is one command of 300 characters at most, so that the record keeps it whole: `python -B -c "..."`, which writes no byte code into the project, or `Rscript -e "..."`. It calls the code of the project on inputs you build in the command. Give it to that line in single quotes, in place of `"<the command>"`.
- Write it to fail on the fault: it asserts what the requirement asks, so its exit code is not 0 while the fault is there. One that fails for another reason, such as a missing package or a typo, proves nothing: fix the probe and run it again.
- Open no data file, and put no value and no name from a dataset into a probe (rule 6). Leave no file in the project (rule 7). A suspicion that one command cannot probe goes under `dropped`, with what was in the way.

## Your verdict block

Write each finding as rule 4 of `verifier.md` says: the record of the probe that failed, a colon, and one sentence that names the requirement it breaks and the line of code where the fault is, written `path:line`, with its priority and `fix:`. After `findings`, give one more list:

```
dropped:
  - <the record of its probe, or none>: <what you suspected, and why the probe did not show it>
```

List there each suspicion you probed that a run did not reproduce, so that the human sees what was tried. A verdict of PASS with its list of dropped is a valid result.

## Leave alone

Style, naming, structure, a risk that needs a future change to matter, and anything you did not run. Say in your note what you did not probe, and why.
