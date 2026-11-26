---
name: brainstorm
derived-from: "addyosmani/agent-skills@e997ac5:skills/idea-refine/SKILL.md; addyosmani/agent-skills@e997ac5:skills/interview-me/SKILL.md; mattpocock/skills@d653911:skills/productivity/grilling/SKILL.md; mattpocock/skills@d653911:skills/engineering/prototype/SKILL.md; cursor/plugins@ca782ed:pstack/skills/poteto-mode/playbooks/prototype.md; cursor/plugins@ca782ed:pstack/skills/sharpen/SKILL.md; cursor/plugins@ca782ed:pstack/skills/reframe/SKILL.md; v1:.agents/commands/cg-brainstorm.md; v1:.agents/commands/cg-ideate.md"
---

# Brainstorm

**You own the shared understanding of what is wanted and which approach to take: look up, ask, widen, narrow, restate, record. The decisions are the human's, and you build nothing.** This playbook changes no file outside `.cg-docs/` except the project's `GLOSSARY.md`, opens no data file, and runs none of the project's code. It ends in a hard stop: the human's yes to the intent as the file reads.

Read `grilling.md` in full before your first question. It is beside the guide's `SKILL.md`. It says how a fact is looked up, how a decision is put to the human, and which replies are not a yes. This playbook says when.

## 1. Start or resume

- If status lists an intent (a file under `.cg-docs/brainstorms/`) with status `draft` under `waiting-on-human`, read each one. When one is about what the human asks now, continue from its open decisions, and do not ask again what it already answers. When it is about something else, leave it as it is and say that it is still open.
- If the human gave nothing to think through, ask what they want to work out, and end your turn.
- Otherwise create the intent, and write into it as you go:

  `"<python>" "<cg>" new intent "<short title>" --project "<project root>"`

The intent is the record of the brainstorm. A later session continues from the file, never from the conversation.

## 2. Look up the facts

Before your first question, find what can be found (P2): the project's `GLOSSARY.md` and README, the code and the documentation the idea touches, the verification profile in `.cg-docs/verification.md`, and earlier intents, plans and decision records under `.cg-docs/` on the same subject. Write each fact you will rely on into the Facts table, with its source.

When the human describes in everyday words something their field has a name for, give the term, one plain sentence on what it means, and a source you opened that uses it that way. Leave out a term you cannot confirm (P7). A term the human takes up goes into the project's `GLOSSARY.md` in the same turn (P11).

## 3. Ask

Say in one sentence what you think the human wants, and what you are still missing. Then ask in rounds, as `grilling.md` says, until you can write Goal, Out of scope and A wrong result in the human's words. End your turn after each round. Add each decision to the Decisions table when you put it, with `open` as its answer, and write the human's answer in when it comes.

## 4. Widen, then narrow

Do this once the goal is clear, and before the human settles on the first approach that came to mind.

**Widen.** Name the approaches that could meet the goal: up to five that differ in kind, fewer when fewer are viable, each in a line or two, each tied to something you found in the project. These questions find them:

- What is the simplest version that still answers the question? What would doing nothing cost?
- Does a package, a function or an output the project already has do this?
- What would an expert in this field do here that was not asked for?
- What is the rawest input to start from, in place of one that is already processed?
- What, other than you or the human, would show that the output is right? The answer also feeds "A wrong result".

**Narrow.** Keep the two or three that really differ. For each, say what it costs, what it risks, and what has to be true for it to work that nobody has checked. When an approach is weak, say so and say why: agreeing with a weak idea helps nobody (P7). When only one approach is viable, present it alone and say why the others fall away. Do not invent alternatives.

**A choice that running something can settle is not a matter of opinion.** In place of a recommendation, name the experiment: the question, the smallest throwaway script that answers it, and the outcome that would favour each option. This playbook does not run it. Running it is a piece of work of its own, which the human starts with `/cg` and whose risk quick work checks. Its outcome comes back here as a fact.

Put the choice of approach to the human as a decision, with the one you recommend and its trade-off. End your turn.

**When a decision waits on an experiment or on someone else,** the brainstorm stops here for now. Leave the intent a `draft` with that decision open, skip steps 5 and 6, and reply as step 7 says. The human comes back to it with `/cg brainstorm` when the answer is in.

## 5. Restate

When no decision is open, fill the rest of the intent: Goal, Out of scope, A wrong result, Assumptions and Approaches considered. Then have code check it:

`"<python>" "<cg>" validate "<the intent>" --project "<project root>"`

A line that starts with `FAIL` or `warn` names what is still open or unfilled. Settle it with the human, or fix it in the file, and run the line again. Go on to step 6 only when it prints `problems: 0` and `warnings: 0`.

## 6. Confirm

This is a hard stop. Show the human the intent as the file reads: the restatement, each decision with their answer, and the assumptions in the block `grilling.md` gives. Ask whether this is what they want. Say that a plain yes confirms it and is recorded under their name, and that you will take anything else as a change or a question. Then end your turn.

When they answer, record the reply before anything else. Show the line, then run it:

`"<python>" "<cg>" approve "<the intent>" --reply "<the human's reply, word for word>" --project "<project root>"`

It sets the intent to `decided`. If it prints `refused`, nothing was recorded. Read the reason: it names the kind of reply, or the part of the intent that is still open, and says what to do. A correction is not a yes: change the intent, show the part that changed, and ask again. Once the intent is `decided`, a change to it needs a new yes.

## 7. Hand over

A brainstorm ends with the intent, not with a change. Do not start the work in the same turn. Commit only when the human asks.

**Reply:** the path of the intent and its status, the goal in one sentence, each decision with the human's answer, the assumptions, the approach they chose and the ones set aside, any experiment or question for someone else that is still to come, what you did not look up, and what the human can do next: once the intent is decided, `/cg plan` for work that needs a plan, or `/cg` with a first change that is small enough for quick work; while it is a draft, `/cg brainstorm` when the answer is in. Label each claim measured, inferred or guess.
