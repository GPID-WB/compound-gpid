---
id: P8
name: The reasoning is the artifact
applies-when: "a decision or a limitation that someone who was not present would need"
stages: "sign-off"
verifier: record
status: draft
derived-from: "docs/philosophy.md (principles 5 and 7); mattpocock/skills@d653911:skills/engineering/domain-modeling/SKILL.md; mattpocock/skills@d653911:skills/productivity/writing-for-agents/SKILL.md; addyosmani/agent-skills@e997ac5:skills/documentation-and-adrs/SKILL.md"
---

# P8 The reasoning is the artifact

The valuable output is the record of reasoning: what the problem was, which approaches were considered, why this one was chosen, and which limits were accepted. It lives in files the team can find. The words it is written in are the subject of P11.

**Why.** Code can run and a table can look clean without the right decisions having been made. If a pitfall is found in one person's chat and nobody else can find it, the organization has not learned.

## In production

### Brainstorm and plan

- Record a decision when it is hard to reverse, surprising without context, and the result of a real trade-off. One paragraph is enough: the choice, the alternatives, the reason.
- Record a rejected idea in `out-of-scope/` with its reason, so it is not proposed again.

### Work

- Commit the artifacts with the code they explain.

### Every stage

- Point, do not restate. Refer to an artifact by its path. Keep each meaning in one place.

## Evidence it leaves

- The linked chain: intent, plan, work report, review, sign-off.
- Decision records and out-of-scope records.

## Verifier: `record`

**Inspect** the artifacts for this piece of work as a reader who was not present.

Flag when you cannot find:

- what the problem was, precisely;
- which approaches were considered;
- why this approach was chosen;
- which risks were known and which limits were accepted.

Also flag when:

- a decision meets all three conditions above and has no record;
- an artifact says something the code contradicts.

**Prove a flag** by pointing at the place the information should be, or at the two places that disagree.

**Leave alone:** decisions that are easy to reverse, and detail the code already makes obvious.

## Deterministic checks

- Every link between artifacts resolves to a file.
- Frontmatter is valid and flat.
