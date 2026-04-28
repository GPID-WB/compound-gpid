# Hooks

This page explains what hooks are, why Compound GPID uses them, and how to work with them — step by step.

> **Current status**: Hooks are in **Phase 0 (proof of concept)**. They are being validated but are not yet part of the day-to-day workflow. You do not need hooks to use any existing `/cg-*` command. This page is here so you understand what they are and how they will work when they ship.

---

## What Are Hooks?

A **hook** is a small script that VS Code runs automatically at a specific moment during a Copilot agent's lifecycle. Think of it like an alarm that goes off at a predefined time — you set it up once, and it fires on its own whenever that moment arrives.

In Compound GPID, hooks are PowerShell scripts (`.ps1` files) that live in `.github/hooks/` inside the project. They are attached to specific Copilot agents and fire when that agent reaches a lifecycle event (for example, when the agent is about to finish its turn).

**Key points:**

- Hooks run **automatically** — you do not invoke them manually.
- Hooks are **agent-scoped** — a hook attached to one agent does not affect any other agent or prompt.
- Hooks can **block or allow** the agent's action (e.g., prevent the agent from stopping too early).
- Hooks communicate via **JSON** — they receive data on standard input and write their response to standard output.
- If a hook fails or encounters an error, it is designed to **fail open** — meaning the agent continues normally rather than crashing.

---

## Why Does Compound GPID Need Hooks?

The Compound GPID workflow loop looks like this:

```
/cg-work → /cg-review → /cg-fix-triage → /cg-compound → commit → PR
```

Today, you invoke each step manually. The long-term goal is a command called `/cg-autopilot` that runs the entire loop for you — you point it at a plan, walk away, and come back to a finished pull request.

For `/cg-autopilot` to work reliably, the system needs a way to prevent the agent from stopping prematurely (for example, after completing only the first step when there are five more to go). That is what the **Stop hook** does: it checks whether the full workflow is complete and, if not, tells the agent to keep going.

Hooks also enable:

- **State preservation**: Before VS Code compacts the conversation to save memory, a hook can save progress to a file on disk so the agent can pick up where it left off.
- **Audit trail**: Hooks log every phase of an autopilot run to `.cg-docs/autopilot-runs/`, so you can inspect exactly what happened.

---

## Hook Types

| Hook Event | When It Fires | What It Does |
|------------|---------------|--------------|
| **Stop** | Just before the agent finishes its turn | Decides whether to **block** (keep the agent running) or **allow** (let it finish). Used to prevent premature termination during multi-step autopilot runs. |
| **PreCompact** | Before VS Code compacts the conversation context | Saves the current progress to a state file so work is not lost. *(Planned for Phase 1 — not yet implemented.)* |

---

## Where Hooks Live

```
your-project/
└── .github/
    └── hooks/
        └── hello-hook-guard.ps1    ← Phase 0 PoC (temporary, will be deleted)
```

In the future, this directory will also contain:

- `autopilot-guard.ps1` — the production Stop hook for `/cg-autopilot`

> **Consumer projects**: The `hooks/` directory is **not yet distributed** to linked projects via `cg-link`. It currently exists only inside the `compound-gpid` repository. Distribution is planned for Phase 1.

---

## How Hooks Are Declared

Hooks are declared in the YAML frontmatter of an agent file (`.agent.md`). Here is what it looks like:

```yaml
---
description: "My agent description"
hooks:
  Stop:
    - type: command
      command: "powershell -ExecutionPolicy Bypass -File .github/hooks/my-hook.ps1"
---
```

Breaking this down:

| Part | Meaning |
|------|---------|
| `hooks:` | Declares that this agent has lifecycle hooks |
| `Stop:` | The lifecycle event to hook into (in this case, when the agent tries to stop) |
| `type: command` | The hook runs an external command (as opposed to other possible hook types in the future) |
| `command: "powershell ..."` | The actual command to execute — here it runs a PowerShell script |

You do **not** need to write this yourself for normal use. The agents that need hooks (`@cg-autopilot`, when it ships) will come pre-configured.

---

## How a Hook Executes (Step by Step)

Here is exactly what happens when a Stop hook fires:

1. **The agent tries to finish its turn.** For example, it has completed a step and is about to stop responding.

2. **VS Code intercepts the stop.** Because the agent has a `Stop` hook declared in its frontmatter, VS Code does not let the agent stop immediately.

3. **VS Code runs the hook script.** It launches PowerShell and executes the script specified in the `command` field. VS Code sends the hook a JSON payload on standard input containing information about the current session.

4. **The hook script reads the payload and makes a decision:**
   - If the workflow is **not complete** → the script outputs a JSON response with `"decision": "block"`, which tells VS Code to prevent the stop. The agent receives the hook's message and continues working.
   - If the workflow **is complete** → the script outputs `{}` (an empty JSON object), which tells VS Code to allow the stop. The agent finishes normally.

5. **The agent either continues or stops**, depending on the hook's response.

```
Agent tries to stop
        │
        ▼
   ┌─────────┐
   │ VS Code  │──── runs hook script ────►  hook reads state
   │ catches  │                              │
   │ the stop │◄── hook responds ───────────┘
   └─────────┘
        │
        ▼
   Block? ──► Agent continues working
   Allow? ──► Agent finishes its turn
```

---

## The Phase 0 Proof of Concept

Before building the full autopilot system, Compound GPID needs to verify that hooks actually work in your VS Code environment. This is what Phase 0 does.

### What Phase 0 Validates

| Test | Question |
|------|----------|
| **A1** | Does the hook fire at all? |
| **A2** | Does the hook receive the expected data from VS Code? |
| **A3** | Can the hook successfully block the agent from stopping? |
| **A4** | Can the hook allow the agent to stop on a second attempt (anti-recursion)? |

### How to Run the Phase 0 Validation

> **Prerequisites**: You must be working inside the `compound-gpid` repository itself (not a linked consumer project).

**Step 1 — Open Copilot Chat**

Open VS Code, then open Copilot Chat (click the Copilot icon in the sidebar, or press `Ctrl+Shift+I`).

**Step 2 — Invoke the test agent**

Type the following in the chat input and press Enter:

```
@cg-hello-hook
```

> Note: `@cg-hello-hook` is a **temporary test agent**. It has no practical use beyond validating that hooks work. It will be deleted from the project after Phase 0 validation completes.

**Step 3 — Watch the agent's behavior**

The agent will:

1. Say it is starting the validation.
2. Try to stop for the first time. If the hook works, VS Code will **block** this stop and the agent will continue.
3. Say the first stop was blocked (A3 passes).
4. Try to stop a second time. This time the hook should **allow** it.
5. Report the results and tell you which files to check.

**Step 4 — Check the log files**

After the agent finishes, open the folder `.cg-docs/autopilot-runs/` in your project. You should see these files:

| File | What It Proves |
|------|----------------|
| `poc-hook-input-<timestamp>.json` | **A1 passes** — the hook fired and received input. Open this file and look for a `stop_hook_active` field to verify **A2**. |
| `poc-hook-output-block.json` | **A3 passes** — the hook blocked the first stop. |
| `poc-hook-output-allow.json` | **A4 passes** — the hook allowed the second stop. |

If all four files exist with the expected content, Phase 0 is validated and the project can move to Phase 1.

### What If It Does Not Work?

- **The agent just stops without being blocked**: The hook did not fire. This may mean your VS Code or Copilot extension version does not support agent-scoped hooks. Check that you are running the latest versions of both.
- **Files are missing from `.cg-docs/autopilot-runs/`**: The hook script may not have had permission to write files. Check your PowerShell execution policy (see Troubleshooting below).
- **The agent gets stuck in an infinite loop**: The anti-recursion guard (`stop_hook_active`) may not be working as expected. Close the chat session and file an issue.

---

## Troubleshooting

### "Script cannot be loaded because running scripts is disabled on this system"

Your machine's PowerShell execution policy is blocking the hook script.

**Fix** (choose one):

1. **For the current user only** — open PowerShell and run:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
2. **Understand what this does**: `RemoteSigned` allows locally-created scripts to run but requires downloaded scripts to be signed. This is a safe setting for development machines.

> The Phase 0 PoC uses `-ExecutionPolicy Bypass` in the hook command to work around this. Production hooks (Phase 1+) will not use `Bypass` — they will either require you to set your policy to `RemoteSigned` or use code-signed scripts.

### "I do not see `.cg-docs/autopilot-runs/`"

The directory is created automatically when the hook first runs. If you do not see it:

1. Make sure you invoked `@cg-hello-hook` (not a different command).
2. Check that you are in the `compound-gpid` repository, not a linked consumer project.
3. Look for error files: `poc-hook-input-error-<timestamp>.json` may contain details about what went wrong.

### "I am in a linked consumer project — how do I test hooks?"

You cannot test hooks in a linked consumer project yet. The `hooks/` directory is not distributed via `cg-link`. Run the validation inside the `compound-gpid` repository.

---

## The Road Ahead

Hooks are being built in phases. Here is what to expect:

| Phase | Status | What Happens |
|-------|--------|--------------|
| **Phase 0** | Current | Proof-of-concept validation. A temporary test agent (`@cg-hello-hook`) verifies that hooks work in VS Code. Temporary files will be deleted after validation passes. |
| **Phase 1** | Planned | Production hook scripts are built. `autopilot-guard.ps1` replaces the PoC. The `hooks/` directory is added to `cg-link` so consumer projects receive it. Scripts are code-signed or require a `RemoteSigned` execution policy. |
| **Phase 2+** | Planned | `/cg-autopilot` ships — the fire-and-forget command that runs the full work → review → fix → compound → commit → PR loop autonomously, with hooks preventing premature stops and preserving state across context compactions. |

> **If hooks turn out to be unsupported** in your VS Code/Copilot version, the fallback is pure prompt-based orchestration (no hooks). The autopilot workflow will still work but without the safety net that prevents the agent from stopping early.

---

## Glossary

| Term | Meaning |
|------|---------|
| **Hook** | A script that VS Code runs automatically at a specific point in an agent's lifecycle |
| **Stop hook** | A hook that fires when the agent is about to finish its turn; can block or allow the stop |
| **PreCompact hook** | A hook that fires before VS Code compacts the conversation; saves state to disk *(planned)* |
| **Agent-scoped** | The hook only fires for the agent it is declared on — it does not affect other agents or prompts |
| **Fail open** | If the hook script crashes or encounters an error, the agent is allowed to continue normally (rather than freezing) |
| **Block response** | A JSON response from the hook that prevents the agent from stopping: `{"hookSpecificOutput": {"decision": "block", ...}}` |
| **Allow response** | An empty JSON response (`{}`) that lets the agent stop normally |
| **Phase 0 PoC** | The current proof-of-concept that validates whether hooks work at all |
| **`@cg-hello-hook`** | The temporary test agent used for Phase 0 validation — will be deleted after validation |
| **`autopilot-guard.ps1`** | The planned production hook script for `/cg-autopilot` *(not yet built)* |
| **State file** | A JSON file in `.cg-docs/autopilot-runs/` that tracks autopilot progress across phases |
| **Anti-recursion guard** | Logic in the hook script that prevents it from blocking the agent forever — after the first block, the second stop is always allowed |

---

## Further Reading

- [Workflow — Hooks section](workflow.md) — how hooks fit into the overall workflow
- [Reference — Agent Hooks](reference.md#agent-hooks) — technical details, file locations, and execution environment
