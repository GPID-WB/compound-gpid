# A typed `/cg` that arrives as the guide's text (gate M1, failure 1)

Evidence for #223, collected on 2026-11-25 by the Fable 5.2 session that reviewed the gate wording.

## What this measures

Failure 1 of the gate: in Kilo's panel and in Posit Assistant, a bare `/cg` did not start the guide. Kilo's session store shows why. The panel sends the body of `SKILL.md` as the human's message, followed by two lines that give the skill's folder, and then whatever the human typed after `/cg`. The words `/cg` are not in the message. The model usually loads the skill with a tool call as well.

`spike/gate/run_cli_gate.py` does not exercise this. From the command line, `kilo run "/cg"` sends the three characters `/cg` (measured in the same store, sessions of the rerun). So the reruns in `rerun-5/` and `rerun-6k/` passed step B on a path that never failed.

The two scripts here send the panel's shape from the command line, in Kilo with `openai/gpt-6-luna`:

- `panel_probe.py` runs steps B to D of `run_cli_gate.py` with the guide message replaced by that shape.
- `panel_b1.py` repeats step B1 alone (a bare `/cg`) on several variants of the guide. Pass: the reply is a setup proposal, nothing is written, and the reply does not tell the human to type `/cg`.

Both are one-off probes run from a scratch folder. Folding them into `run_cli_gate.py` is noted on #223 for Opus 5.5. `panel_b1.py` writes each variant over the installed `SKILL.md`; run `install.py --update --force` afterwards.

## Results

A bare `/cg` in the panel's shape, by the text of section 2 of the guide:

| Section 2 | Commit | Passed |
|---|---|---|
| As Opus 5.5 wrote it for the gate | `e624bca5` | 2 of 4 |
| First rewrite: three cases in order | `0c7324c1` | 3 of 4 |
| Second rewrite: decided from the human's message alone | `0f55a8ed` | 10 of 10 |

The four runs of the first two rows are one full probe each (`before-e624bca5/`, `after-25dc5642/`) and three repeats each (`b1-three-variants/`, files `opus-*` and `v1-*`). In `b1-three-variants/` the three texts differ in section 2 only; everything else is the guide at `25dc5642`. The files `v2-*` there are the second rewrite, before one sentence on the pointer block was added below the table.

In every failure the reply was the last row of section 2: the state in two lines, then "Type `/cg` to start the guide". In every run, pass or fail, the model had also loaded the skill with its own tool call.

The ten runs of the third row are the three `v2-*` files in `b1-three-variants/`, and in `final/` six repeats (`b1-*`) and one full probe (`kilo-panel.md`, 9 of 9 from B to D) on the text of `d93dfef6`.

Not fixed: with a request after `/cg` in the panel's shape, Kilo still opened its reply with the pointer block's sentence, "`/cg` would run this change with checks and a record", and then ran the guide (`final/kilo-panel.md`, step C1). From the command line, where the message holds `/cg`, it no longer does (`../rerun-8/kilo.md`).

These are small samples from one model in one coding agent. They show that the path is not reliable with the first two texts. They do not show that it is reliable with the third. Kilo's panel and Posit Assistant themselves were not run; the maintainer checks a bare `/cg` there.

## Reading the transcripts

Local paths and the user name are removed. The guide's text, which each prompt quotes in full, is replaced by a one-line marker.
