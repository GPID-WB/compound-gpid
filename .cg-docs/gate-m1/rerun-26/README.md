# Gate rerun 26

Run on `d79ed87d`: task 2.9 as reviewed, with the gate check of #259 (each approval holds the reply of its turn and
a text the agent showed before it). Codex and the two Kilo shapes, one after the other. Claude Code was left out to
save the account's Fable 5.2 limit.

- Kilo: 50 of 50, every step, step R and the new check included.
- Codex: 43 of 50.
  - Step C: `tier` found six files, and quick work sends a change of that size to a plan, so the agent opened a
    brainstorm and the function was never written. The agent followed the text.
  - The new check, step W, turns W6 and W8: after the human's "Yes." the agent wrote the dated line under
    `## Amendments`, which `approve` needs, and then recorded the yes, so the approved text was not the one shown.
    In W6 it had also put the new commands under Amendments and left the table of checks as it was, so `evidence`
    ran the old command and a second approval was needed. The check caught a real departure from "for what was
    shown and nothing more"; the text should say to write the dated line before asking.
  - The new check, step X, turn X2: a false alarm. The agent showed the agreement for the deletion but named neither
    the work report's file nor its title, which the weak part of the check asks for.
- Kilo with the panel's shape: 31 of 49. As in rerun 25, in step B it asked for the data decisions first and then
  for a second yes to the proposal, the script's two turns ran out before setup was written, and the later steps
  failed in turn.

The transcripts were cleaned by the sanitizer of `d2eafc91`; none holds a name, an address or a home folder.
