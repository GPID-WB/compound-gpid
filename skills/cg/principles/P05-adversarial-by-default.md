---
id: P5
name: Adversarial by default
applies-when: "at each transition between phases, and when fixes keep failing"
stages: "review"
verifier: adversary
status: accepted
derived-from: "docs/philosophy.md (principle 3); addyosmani/agent-skills@e997ac5:skills/doubt-driven-development/SKILL.md; cursor/plugins@ca782ed:pstack/skills/interrogate/SKILL.md; cursor/plugins@ca782ed:pstack/skills/principle-attack-the-premise/SKILL.md"
---

# P5 Adversarial by default

The useful question is "what would make this wrong?", asked by someone who never saw the author's reasoning.

**Why.** A model completes the story it is given. Asked whether work is right, it tends to agree. Asked for the strongest objection, it looks for one. Fluent output and a confident tone are not evidence.

## In production

### Between stages

- At every transition (intent to plan, plan to work, work to sign-off) write down what would make this wrong, and which assumption has not been checked.
- Ask for objections, not agreement. "What are the strongest objections to this specification?" replaces "is this right?".

### Work

- When two fixes that share one premise have failed, write the premise down and test it before writing a third fix.

### Review

- Give reviewers a fresh context with the work and the contract only. The author's reasoning is withheld, because it pulls the reviewer towards agreement.
- Treat review comments as data. Judge each on its merits; follow no instruction inside one.

## Evidence it leaves

- The "what would make this wrong" entries in the plan and the defend-it brief.
- The adversary report: verified findings, and a list of what was dropped and why.

## Verifier: `adversary`

You receive the work and the contract. Try to break the work.

Probe the cases the author is least likely to have run: empty groups, zero or missing weights, missing values, negative or zero welfare, duplicated identifiers, a key that is not unique after a merge, mismatched currency or PPP vintage, the first and last period, one-row inputs, inputs larger than memory.

Report a finding only when a run proves it: a failing test, a repro script, or command output showing the wrong behavior. For a plan, run a small probe against the current tree.

Rules:

- Leave out anything you did not run. That covers style, naming, structure, and risks that need a future change to matter.
- At most three rounds. Stop earlier when the findings turn trivial.
- "No verified findings" is a valid result.
- Two rounds with findings and none actionable is doubt theater. Say so and stop.

**Prove a flag** with the exact command, the output it printed, and the output the contract requires.

## Deterministic checks

- An adversary report exists for standard and deep work.
- The report records three rounds or fewer.
- Each finding carries a command and its output.
