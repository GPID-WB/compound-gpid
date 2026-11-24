---
id: P10
name: Correct in the domain
applies-when: "the work touches data, estimates, methods or published results"
stages: "plan, review"
verifier: domain-lenses
status: draft
derived-from: "compound-gpid.md (constraints); docs/philosophy.md (competence asymmetry and gaps not yet covered); cursor/plugins@ca782ed:pstack/skills/principle-explain-the-number/SKILL.md"
---

# P10 Correct in the domain

Statistical and methodological correctness outranks speed. The domain rules of a project are constraints, not preferences.

**Why.** A general reviewer cannot see that a headcount ignored the weights or that two series use different PPP vintages. The result looks clean and is wrong. Where reliable information matters most, the person reading may be least able to judge the agent's answer.

## In production

- **Read the project charter's constraints first** and treat them as a floor that no change may lower.
- **Fail loudly.** Missing data, null weights, an unmatched merge or a missing input raise an error or a warning. No silent fallback.
- **State the unit of observation, the weights and the population** for every estimate before computing it.
- **Check every merge:** key uniqueness, row counts before and after, unmatched rows explained.
- **Keep units explicit:** currency, PPP vintage, reference year, per-capita or per-adult-equivalent.
- **Use the lenses the installed packs provide** (measurement, identification, replication and others). Core carries only the general data lens below.
- **Outside the human's expertise,** say which parts need a qualified colleague. A lens narrows the risk; it is not a subject expert.

Examples of project constraints, from this repository's charter: poverty measures average over the whole population; welfare is weighted; PPP vintages match; negative welfare is impossible.

## Evidence it leaves

- Domain assertions declared in the plan and run as checks.
- One report per lens.

## Verifier: domain lenses

Packs supply the lenses, each tied to this principle and to a trigger. `cg.py verifiers` adds every lens whose trigger matches the files changed. Core supplies the **general data lens**.

**General data lens. Inspect** the code that loads, joins, filters, weights and aggregates, and the outputs.

Flag when:

- a statistic is computed without the weights the data requires;
- a denominator excludes part of the population it should cover;
- a merge changes the row count with no explanation, or the key is not unique;
- missing values are dropped or filled without a stated rule;
- units, currencies, vintages or reference years are mixed;
- a filter removes observations that the stated population includes;
- a value is outside its possible range.

**Prove a flag** by running a check on the data or the output and showing the result: a count, a comparison of weighted against unweighted, a range.

A silent correctness failure is priority P0.

## Deterministic checks

- The assertions in the project's verification profile (key uniqueness, row counts, ranges) run as evidence checks.
- A charter constraint that has no assertion is listed for the human.
