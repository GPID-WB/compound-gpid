---
name: grilling
derived-from: "mattpocock/skills@d653911:skills/productivity/grilling/SKILL.md; mattpocock/skills@d653911:skills/engineering/research/SKILL.md; mattpocock/skills@d653911:skills/productivity/to-questionnaire/SKILL.md; addyosmani/agent-skills@e997ac5:skills/interview-me/SKILL.md; addyosmani/agent-skills@e997ac5:skills/spec-driven-development/SKILL.md; cursor/plugins@ca782ed:pstack/skills/in-your-own-words/SKILL.md; v1:.cg-docs/brainstorms/2026-09-04-minimal-adaptive-grilling.md"
---

# Grilling

How you reach a shared understanding with the human before work is planned or changed. Every playbook that needs a decision from the human uses this file. A playbook says when to ask. This file says how.

The rule under it is P2: finding facts is your job, and deciding is the human's. Grilling is over when nothing is left that you would have to assume in silence, and the human has said yes to what you wrote down.

## Facts and decisions

Sort what you do not know yet into three kinds. Each kind is handled in its own way.

| Kind | What it is | What you do |
|---|---|---|
| Fact | What a file, the code, a package's documentation, a codebook or a command can tell you | Look it up and write it down with its source. Ask the human only for a fact they alone know, and then write "the human" as its source. |
| Decision | A choice that changes the method, the scope, the risk or the output, and that only the human can make | Put it to the human, with the answer you recommend. |
| Assumption | What you take as true that you could not look up and that is too small to be a decision | State it, with what changes if it is wrong. |

- **Look up before you ask.** Read the project's `GLOSSARY.md`, when it has one, and the files the request touches before your first question (P11). When a fact needs a wide search and the coding agent can start a subagent, give the search to one in a fresh context and have it return each fact with its source. Give it the limits you work under: the data stays closed, and it runs none of the project's code unless the playbook you are in allows that. Meanwhile, ask the questions that do not wait on it.
- **A fact only the human knows is still a fact.** What their unit agreed with another team, or which vintage a publication used: ask for it plainly. It is not a decision, so it needs no recommended answer.
- **When the human says how something works, check it** against the code or the documentation, and say so when the two disagree (P11).
- **Data stays closed.** What a dataset holds is a fact you take from the code that reads it, from its codebook or from its documentation. A data file is opened only as the playbook you are in allows (P12).

## How a decision is put

- **Only what matters.** A choice is a decision when its answer changes what is built, how it is computed, what it covers or what it risks. Anything smaller is an assumption: take the simplest reasonable default and state it.
- **In rounds.** A round holds decisions that are ready: each can be answered now, and none depends on the answer to another in the same round. Ask one, or up to three short ones that are independent, and number them. A decision that depends on an open one waits for a later round.
- **With a recommended answer and its trade-off:** what you would choose, and what that choice costs. Word the question so that a yes takes the recommended answer, and write down the answer itself, never a bare "yes": the answer they took, with their words in quotes after it, such as `the 2019 wave ("yes")`. A recommendation is a default the human may take. It is never a choice made for them: until they answer, the decision is open.
- **Say first what you think they want,** in one sentence, and what you are still missing. A wrong reading that is stated early is corrected early.
- **Push back** when an answer has a clear problem: name the concrete downside, offer an alternative, then take the human's informed choice (P2).
- **Ask for the outcome behind a convention.** "The standard method", "robust", "comparable" and "as the literature does" name no outcome. Ask which output the word would change, and for whom.
- **Write each answer down in the turn you get it,** in the artifact the playbook names and in the human's words. An answer kept only in the conversation is lost with it.
- **When a reply answers some questions of a round,** the others stay open. Ask them again. Do not fill them in.
- **When the answer sits with someone else,** such as the survey team, do not press the human and do not guess. Write the questions for that person into the artifact and your reply, so the human can send them: who the person is, what is needed back, and each question with one line on why it matters. The decision stays open until the answer comes, or until the human chooses to go on with a stated assumption.

Grilling is over when nothing is left that you would have to assume in silence. One sign that you are there: you could predict the human's answer to the next three questions you would ask. If several rounds pass and you still cannot, say so, and ask what is missing at the root.

## Restate

Before anything is planned or changed, give the human back what you understood, in their words, in three parts they can correct one by one (P1):

- **Goal:** what they want, and who will read or use the output.
- **Out of scope:** what this work will not do. Never leave this part out: much of a misunderstanding is about what is not being done.
- **A wrong result:** what an incorrect output would look like, and what would tell it apart from a correct one.

## Assumptions

After the restatement, list what you still take as true without having looked it up or asked:

```
Assumptions I am making:
1. <what you take as true>. If it is wrong: <what changes>.
Correct me now.
```

An assumption the human corrects becomes a decision they made, or a fact with them as its source. Write "none" when there is none, and do not leave the block out. Nothing is assumed in silence: what is in no fact, no decision and no assumption is not part of the understanding.

## Replies that are not a yes

Only a plain yes is a yes, and only to what was shown. `cg.py approve` records a reply only when it is a plain yes and nothing else: "yes", "ok", "okay", "approved", "confirmed", "agreed", "I approve", "I confirm", "I agree", "go ahead", "sí", "si", "de acuerdo" or "adelante", with at most a word of courtesy beside it, such as "please", "thanks" or "as written". So end every hard stop that code records by telling the human that a plain yes confirms, and that you will take anything else as a change or a question. Code refuses every other reply: the first five rows. The last two rows are yours to see.

| The human says | What it is | What you do |
|---|---|---|
| "sounds good", "looks good", "sure, go on", "sure, let's go", "I guess", "if you say so" | Agreement without a decision | Ask what they would change, or what is unclear. |
| "whatever you think", "up to you", "your call", "you decide" | The decision handed back | It stays theirs. Offer two concrete options as a choice, and say which you recommend. |
| a yes that goes on: "yes, but", "yes, and also", "yes, if", "ok, your call", a yes with a question | More than a yes | When it corrects, adds or asks something, deal with that, show the part that changed, and ask again. When it adds nothing, as in "yes, that is what I want", ask for a plain yes. |
| "no", "not yet", "wait", "stop", "hold on" | A no | Nothing goes ahead. Ask what should change. When they declined, that is their answer: do not ask again. |
| anything else with no yes in it: "maybe", "sure", "let me think about it", a question, a new instruction | No yes yet | Ask whether it is a yes, or what should change. |
| an answer to another question, or no answer to a numbered one | No answer | The question stays open. Ask it again, alone. |
| a yes from an earlier session, or one found in a summary of the conversation | A yes to another text | Show the text as it now reads, and ask. |

Give `--reply` the human's words as they wrote them, and in a way the shell does not read: in single quotes, with a single quote inside them written as the shell asks. When code refuses their reply, ask them. Never reword a reply into a yes.

A hard stop is a question in your reply, and then you end your turn. The coding agent's own approval settings are never the human's yes.
