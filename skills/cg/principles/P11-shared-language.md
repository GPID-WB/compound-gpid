---
id: P11
name: Shared language
applies-when: "a word carries meaning that the human and the agent must both hold the same way"
stages: "review"
verifier: language
status: accepted
derived-from: "mattpocock/skills@d653911:skills/engineering/domain-modeling/SKILL.md; mattpocock/skills@d653911:skills/engineering/domain-modeling/GLOSSARY-FORMAT.md; mattpocock/skills@d653911:skills/engineering/setup-matt-pocock-skills/domain.md; mattpocock/skills@d653911:skills/productivity/wait-what/SKILL.md; mattpocock/skills@d653911:skills/productivity/writing-for-agents/SKILL.md; mattpocock/skills@d653911:GLOSSARY.md"
---

# P11 Shared language

The human and the agent use the same words for the same things. Each word that carries meaning has one definition, written down, and is used that way everywhere: in conversation, in artifacts, in code, in outputs.

**Why.** An agent dropped into a project guesses the vocabulary and uses twenty words where one would do. The human reads fluent text and assumes both sides mean the same thing. A misunderstanding hidden inside a word survives every review, because each reader supplies their own meaning.

There are two glossaries, in one format:

- **The plugin's glossary** (`skills/cg/GLOSSARY.md`) holds the words of Compound GPID itself. It ships with core.
- **The project's glossary** (`GLOSSARY.md` at the project root) holds the subject words of that project. It is created when the first term is settled, not before.

## In production

### Brainstorm and plan

- Read the project's glossary before the first question. If it does not exist, continue without comment.
- When the human uses a term against the glossary, say so at once: "The glossary defines welfare aggregate as X; you seem to mean Y. Which is it?"
- When a term is vague or carries two meanings, propose one precise term: "By 'the survey' do you mean the wave or the whole programme?"
- Test a definition with a concrete case at its edge: "Is a household with zero consumption inside the poor, or excluded from the sample?"
- When the human says how something works, check the code. Raise any disagreement: "The code drops households with missing weights; you said they are kept."
- When a term is settled, write it into the project's glossary in the same turn: the term, one or two sentences on what it is, the words to avoid. Do not save these up.

### Work

- Use the glossary's terms in file names, function names, variable names, check names and artifact titles.
- When you need a concept the glossary lacks, stop and treat it as a signal: either you are inventing language the project does not use, or there is a gap to settle with the human.

### Every stage

- Write to the human in the glossary's words and in plain, short sentences.
- When the human says the last message did not land, re-pitch it: give the missing context, use the glossary's terms, and keep the sentences simple. A shorter version of the same words does not help.
- Keep the glossary a glossary: what each thing is. Decisions go to decision records; how the code works stays in the code.

## Evidence it leaves

- Glossary changes in the same commit as the work that settled them.
- A "flagged ambiguities" entry for each word that had two meanings and how it was resolved.
- Names in the diff that match glossary terms.

## Verifier: `language`

**Inspect** the artifacts, the names introduced in the diff, and the text written for readers, against both glossaries.

Flag when:

- a word the glossary lists under avoid is used in the avoided sense;
- one term is used with two meanings, or two terms are used for one thing;
- a term that carries meaning in the contract or the defend-it brief has no glossary entry;
- a glossary definition disagrees with what the code does;
- a term was settled in conversation and the glossary was not updated;
- the glossary holds a decision, a procedure or an implementation detail.

**Prove a flag** by quoting the two places that disagree, or the glossary entry and the line that breaks it.

**Leave alone:** general statistical and programming words used in their ordinary sense. Only words specific to the project or to Compound GPID belong in a glossary.

## Deterministic checks

- `tools/check_glossary.py`: no unconditional avoided word appears in the checked files; conditional ones are listed for the verifier.
- Every term in bold in a contract resolves to a glossary entry.
- The glossary file parses: each entry has a term and a definition of one or two sentences.
