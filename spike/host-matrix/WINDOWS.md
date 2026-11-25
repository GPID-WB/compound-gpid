# Host matrix on Windows: handoff for the agent

For a coding agent on a Windows machine, started by the human with: "Read `spike/host-matrix/WINDOWS.md` and do what it says."

You are helping test how coding agent hosts behave on Windows (issue #211). You run one script three times, help the human with a short test in the editor, and push a few report files. You own getting clean results back to the repository. You do not fix, build or tidy anything else.

## Before you start

Check these and stop with a clear message if one fails.

1. `git branch --show-current` prints `v2`.
2. The repository folder is not inside OneDrive (`git rev-parse --show-toplevel` has no `OneDrive` in it). Switching branches inside a synced folder has deleted files before. If it is inside OneDrive, ask the human to make a fresh copy somewhere else and start again there:
   ```
   git clone --branch v2 --single-branch https://github.com/GPID-WB/compound-gpid C:\dev\compound-gpid
   ```
3. `py -3 --version` works. If not, try `python --version`, and use whichever works in every command below. Tell the human which one worked; that is a result too.

## Boundaries

- Change files only under `spike/host-matrix/reports/`.
- Do not switch branches, and do not touch `main`, `v1`, `dev` or any tag.
- The script starts the Claude Code, Codex and Kilo command-line programs and uses a small amount of each account's quota. If your host refuses to let you start them, do not look for another way. Give the human the command to run in PowerShell, wait, then continue from the reports.
- Everything pushed here is public. Push nothing that names a person, an email address, a machine or an internal address.

## Step 1: three runs

Each run takes a few minutes, prints `>> <name>` as it goes, and ends by printing the report file it wrote. Run them one at a time from the repository root.

| Run | Command | What it tests |
|---|---|---|
| A | `py -3 spike\host-matrix\run_cli_checks.py --kilo-model openai/gpt-6.2-sol --report` | The same checks already run on macOS |
| B | `py -3 spike\host-matrix\run_cli_checks.py --kilo-model openai/gpt-6.2-sol --report --project-parent "<OneDrive folder>\Documents"` | A project inside OneDrive, with spaces in its path |
| C | `py -3 spike\host-matrix\run_cli_checks.py --kilo-model openai/gpt-6.2-sol --report --layout copy` | A real copy of each skill in both user-level folders, which is what an installer must do where links are not allowed |

For run B, `<OneDrive folder>` is the value of `$env:OneDriveCommercial`, or `$env:OneDrive` if the first is empty. The script makes one small folder there and removes it at the end. Skip run B if neither is set, and say so.

If Kilo's answers say that credits are needed or that the model cannot call tools, ask the human which model their Kilo account can use, and rerun with `--only kilo --kilo-model <provider/model>`.

A program reported as "Not found on this machine" is a result, not an error. Do not install anything.

## Step 2: read the reports

Open each new file in `spike\host-matrix\reports\`. For each program, find the answers to these and keep them for your reply:

- Is each `cg-spike` skill listed, and listed once?
- Did `/cg-spike-hello` run the script? Which Python command did the program use?
- Did "I saw a purple heron today" start `cg-spike-auto`?
- Did "Please run the host probe" start `cg-spike-hello`, although only the human should be able to?
- Which marker was loaded: `CG-SPIKE-POINTER-AGENTS`, `CG-SPIKE-POINTER-CLAUDE`, or both?
- In `claude-5-import`: is `CG-SPIKE-POINTER-AGENTS` present?
- What does `run-info` say under `skill layout`? On Windows it shows whether a link was allowed.

The script already replaced local paths, the user name and email addresses. Read every report once more for anything it could not know about: a colleague's name, a machine name, an internal web address. If you find one, replace it with `<removed>` and tell the human what you replaced.

## Step 3: the test only the human can do

Two hosts run only inside the editor: Copilot, and Kilo's own panel. Prepare the test, then hand over.

1. Install the test skills:
   ```
   New-Item -ItemType Directory -Force "$HOME\.agents\skills" | Out-Null
   Copy-Item -Recurse -Force spike\host-matrix\skills\cg-spike-* "$HOME\.agents\skills\"
   ```
2. Ask the human to do tests 1 to 5 of `spike/host-matrix/CHECKLIST.md` in a new Copilot chat and a new Kilo chat, in any project whose `AGENTS.md` holds the line `CG-SPIKE-POINTER`, and to count the approval prompts they see. The editor may need a restart before the skills appear.
3. Write what the human reports, in their words, to `spike\host-matrix\reports\windows-manual.txt`, one block per host, with the host's version and the model used.
4. Remove the test skills:
   ```
   Remove-Item -Recurse -Force "$HOME\.agents\skills\cg-spike-hello", "$HOME\.agents\skills\cg-spike-auto"
   ```

If the human has no time for this step, skip it and say it is still open.

## Step 4: push

```
git status --short
```

Only files under `spike/host-matrix/reports/` may appear. If anything else does, stop and tell the human. Then:

```
git add spike/host-matrix/reports
git commit -m "test(spike): host matrix results on Windows"
git pull --rebase origin v2
git push origin v2
```

If the pull or the push fails, stop and show the human the message. Do not force anything.

## Reply

End with one message to the human that holds:

- the commit you pushed, or why nothing was pushed;
- one line per program and run: found or not, and the answers from step 2;
- anything that differed from this note: a command that failed, a prompt that timed out, something you replaced in a report;
- what is still open.

The build session on the other machine reads the reports from `v2` and updates `docs/adr/0001-host-matrix.md`. Do not edit that file here.
