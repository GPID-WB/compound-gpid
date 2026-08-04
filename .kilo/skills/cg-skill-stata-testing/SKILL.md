---
name: cg-skill-stata-testing
user-invokable: false
description: >
  Testing and reproducibility best practices for Stata. Covers inline
  assertions (assert, capture, exit codes), data validation patterns
  (isid, duplicates, misstable), econometric result verification (reldif,
  _b[], test), reprun/repkit reproducibility workflows, test scaffolding
  (foreach loops, preserve/restore), and testing anti-patterns with fixes.
  Load when writing, reviewing, or debugging assertion blocks, data validation,
  result verification, test scaffolding, or reproducibility checks in .do/.ado files.
  Use alongside cg-skill-stata-best-practices for coding principles and
  package reference.
---

# Stata Testing & Reproducibility Skill

You have access to Stata testing reference files. **Do not load all files.**
Read only the 1–2 files relevant to the user's current task using the routing
table below.

> **Comment style**: Code examples use `*` for inline comments. In project `.do` files, use `//`
> as the default inline comment style per `stata.instructions.md` (`*` is reserved for section delimiters).

**Cross-references**:
- `cg-skill-stata-best-practices` —
  coding principles, repkit API docs, all 21 community packages
- `cg-skill-r-testing` —
  R testing patterns for Stata→R migration context

---

## Routing Table

| File | Topics & Key Commands |
|------|-----------------------|
| [`references/assertions-and-error-handling.md`](references/assertions-and-error-handling.md) | `assert`, `capture`, `_rc`, exit codes, soft assertions, structured assertion blocks |
| [`references/data-validation.md`](references/data-validation.md) | `isid`, `duplicates`, `misstable`, `inrange`, panel structure, survey design, type safety |
| [`references/result-verification.md`](references/result-verification.md) | `_b[]`, `reldif`, `test`, coefficient bounds, sign checks, FGT index checks |
| [`references/reproducibility-reprun.md`](references/reproducibility-reprun.md) | `reprun`/`reproot`/`repscan` testing patterns (full repkit API → `cg-skill-stata-best-practices`), `set seed`, result caching |
| [`references/test-scaffolding.md`](references/test-scaffolding.md) | `foreach` loops, `preserve`/`restore`, `tempfile`, test harness, pass/fail reporting |
| [`references/anti-patterns.md`](references/anti-patterns.md) | 9 testing-specific anti-patterns with ❌ wrong / ✅ correct patterns and explanations |
| [`references/workflow-examples.md`](references/workflow-examples.md) | End-to-end examples: poverty FGT, PPP conversion, survey estimates, DiD testing |
