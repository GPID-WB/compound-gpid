---
name: language
principle: P11
derived-from: "mattpocock/skills@d653911:skills/engineering/domain-modeling/SKILL.md; mattpocock/skills@d653911:skills/engineering/code-review/SKILL.md; addyosmani/agent-skills@e997ac5:skills/code-review-and-quality/SKILL.md; v1:.agents/skills/cg-code-quality.md; v1:.agents/skills/cg-documentation.md"
---

# Lens: language

This lens is for the verifier of P11. It says what code holds, what is left to your judgement, how each flag is proved and the change each fix proposes. It adds to the section "Verifier" of your principle file and takes nothing from it.

## What code holds

- No rule of code reads a project's words. The project's glossary is `GLOSSARY.md` at its root, when there is one, and the plugin's is beside the guide.
- A rule of style that a linter checks, such as `lintr`, `styler` or `ruff`, belongs to the linter, as a check of the plan or of the verification profile (P3): leave it. So does a rule that the lead skill of a language pack sets, such as the R dialect of `r-shared`.
- Read the change (`git diff` against the commit your kickoff names), the text written for readers that it touches, and both glossaries.

## The flags

| Flag | You judge | Fix: the change to propose | Priority |
|---|---|---|---|
| A word the glossary says to avoid | in a name, a help page, a README, an artifact or the work report, in the sense the glossary rules out | the glossary's term | P2 |
| One term with two meanings, or two terms for one thing | a column, a function, a file, a check or a sentence that names one thing two ways, or two things one way | one term, the glossary's, everywhere the change uses it | P2 |
| A text that says what the code does not do | a help page, a docstring, a roxygen `@param` or `@return`, a README line or a comment that names an argument that is gone, a default or a return value that changed, or a unit the code does not use | the text that says what the code does, or the code the contract asks for | P1 |
| Text left behind a changed function | an argument added, renamed or removed, or an exported function added, with no change to its help page; in R, `man/` not written again | the help page changed with the code; in R, `devtools::document()` | P2 |
| A name that tells a reader nothing | `df2`, `tmp`, `x_new`, `data` or `result` with no context, or a name that says how and not what | a name in the glossary's words that says what it holds | P3 |
| A term the contract leans on with no entry | a word of the contract or the work report that carries meaning and that no glossary defines | an entry in the project's glossary, in the same commit | P3 |
| A glossary that holds a decision or a procedure | an entry that says why, how or who, beside what the thing is | the decision in a decision record; the entry says what the thing is | P3 |

## Prove and propose

- Point at the line that uses the term or says what the code does not do, and name in your sentence the glossary entry or the line of code it disagrees with, written `path:line` (rule 4 of `verifier.md`).
- Write each finding with the priority of its row and `fix:` with the change of its row, written for this line.
- Copy no value of a dataset and no person's name into a finding: a column name is enough (rule 6).

## Leave alone

General statistical and programming words in their ordinary sense, spelling, a name the human chose in the plan, and a matter of taste. Duplicated code and an abstraction nobody needs are P6's. Say in your note what you left and why.
