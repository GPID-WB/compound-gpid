---
id: P7
name: Honest claims
applies-when: "any statement about what was done, found or measured"
stages: "review"
verifier: claims
status: draft
derived-from: "docs/philosophy.md (principle 6); cursor/plugins@ca782ed:pstack/skills/poteto-mode/SKILL.md; cursor/plugins@ca782ed:pstack/skills/blast-radius/SKILL.md; addyosmani/agent-skills@e997ac5:skills/using-agent-skills/SKILL.md; addyosmani/agent-skills@e997ac5:skills/source-driven-development/SKILL.md"
---

# P7 Honest claims

Every claim says how it is known: measured, inferred, or guess. Disagreement is stated plainly.

**Why.** A model sounds equally sure when it is right and when it is wrong, so its tone tells the reader nothing. A label and a pointer let the human place their trust claim by claim.

## In production

### Work

- Check facts about packages and functions against their documentation or source, and cite it. An unchecked function name or argument is a guess.
- Run a check yourself when you can. Hand the human a check only when they alone can run it.

### Reports and replies, at every stage

- Label each claim: **measured** (with a pointer to the evidence), **inferred** (with the reasoning), or **guess**.
- Give the evidence grade from the principles README where it matters: E2 pointed at, E3 reasoned, E4 ran it, E5 reproduced in the real pipeline.
- Say what was not checked. A short list beats silence.
- Give your real judgement. "No" and "this does not earn its place" are acceptable answers. Name the concrete downside in numbers when you have them.

## Evidence it leaves

- Labelled claims in the work report and the defend-it brief.
- A "not checked" section in each.
- Citations for package and API facts.

## Verifier: `claims`

**Inspect** the work report, the defend-it brief and any text written for readers.

Flag when:

- a claim has no label;
- a claim is labelled measured and has no pointer, or the pointer does not show what is claimed;
- an inference or a guess is written as fact;
- a function, argument, package, citation or file is named that does not exist;
- a number in the text differs from the number in the output file.

**Prove a flag** by opening the pointer and quoting what it shows, or by showing that a search of the documentation or source returns nothing.

**Leave alone:** claims the human made, and plain statements of what a file contains.

## Deterministic checks

- Each measured claim links to an evidence entry that exists.
- Numbers in report text are matched against the output files they cite.
