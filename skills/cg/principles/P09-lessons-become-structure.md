---
id: P9
name: Lessons become structure
applies-when: "capturing what was learned, or writing the same instruction a second time"
stages: "compound"
verifier: lesson
status: draft
derived-from: "cursor/plugins@ca782ed:pstack/skills/principle-encode-lessons-in-structure/SKILL.md; cursor/plugins@ca782ed:pstack/skills/correct/SKILL.md; cursor/plugins@ca782ed:pstack/skills/reflect/SKILL.md; mattpocock/skills@d653911:skills/engineering/retro/SKILL.md; EveryInc compound engineering (the compound step)"
---

# P9 Lessons become structure

Each unit of work should make the next one easier. A verified lesson becomes a check first and prose second.

**Why.** Nothing fails when an agent or a person skips a written rule. A check fails loudly. A rule written twice is a sign the first writing did not work.

## In production

- **Capture a lesson only if** the fix was verified, the lesson will still hold in six months, and it would change what someone does next time.
- **Leave out** one-off details that drift: commit hashes, versions, counts.
- **Classify it.** A mechanical lesson (a fixed pattern, a banned call, a required column, a file location) gets a check. A judgement call gets prose for the reviewer.
- **Fix at the highest level that works:**
  1. change the design so the mistake cannot happen;
  2. a type, a schema or an assertion at the boundary;
  3. a lint or CI check whose message names the fix;
  4. a test of the behavior;
  5. written guidance, last, only for judgement.
- **Prove the check** by showing it fails on the real past mistake.
- **Keep the rule table:** each rule beside what enforces it. Remove a rule once its mistake cannot happen.
- **Count a class** once it has happened twice.

## Evidence it leaves

- The solution record, linked to the evidence that the fix worked.
- The new check in the diff, and the run showing it fail on the old mistake.
- The rule table row.

## Verifier: `lesson`

**Inspect** each lesson proposed for capture.

Flag when:

- the fix behind the lesson was never verified;
- an existing record already says it;
- a mechanical lesson was left as prose;
- a new check passes on the mistake it is meant to catch;
- the record holds details that will be stale within months.

**Prove a flag** by pointing at the existing record, or by running the new check against the past mistake and showing the result.

**Leave alone:** judgement calls that truly cannot be checked by code.

## Deterministic checks

- The solution record links to an evidence entry that exists.
- A search of existing records by title and tags for duplicates.
- Stale detection: records whose referenced files changed or vanished since capture.
