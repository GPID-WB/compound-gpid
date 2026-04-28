---
description: "Temporary PoC -- validates VS Code Copilot agent-scoped Stop hook behavior. Delete after Phase 0 validation."
model: Claude Sonnet 4.6 (copilot)
tools: ['read']
user-invocable: false
hooks:
  Stop:
    - type: command
      command: "powershell -ExecutionPolicy Bypass -File .github/hooks/hello-hook-guard.ps1"
---

# Hello Hook PoC

> **TEMPORARY AGENT** — used only for Phase 0 hook API validation. Delete after validation.

> **Phase 1 note**: The `-ExecutionPolicy Bypass` flag in the hook command overrides the machine execution policy. For any permanent hook infrastructure (Phase 1+), scripts should be code-signed, or consumers must configure their execution policy to `RemoteSigned`. Do not ship permanent hook scripts with `-ExecutionPolicy Bypass`. This is a Phase 1 acceptance criterion.

You are validating whether VS Code Copilot agent-scoped Stop hooks work correctly.

**Step 1**: Say exactly: "Hello! Starting Stop hook PoC validation. About to attempt first stop."

**Step 2**: Attempt to complete/stop your response now.

> If the Stop hook fires correctly, it will block you. You should receive a message
> from the hook and continue to Step 3. If you are NOT blocked and simply stop here,
> it means the hook did not fire (A3 fails — hooks may not be supported in this environment).

**Step 3**: Say exactly: "The hook blocked the first stop (A3 pass). Now attempting second stop."

**Step 4**: Attempt to complete/stop your response again.

> On the second attempt, the hook should receive `stop_hook_active: true` and allow the stop.
> If you reach Step 5, the anti-recursion guard worked.

**Step 5**: Say exactly: "Second stop was allowed (A4 pass). PoC complete. Check these files in `.cg-docs/autopilot-runs/` to validate assumptions:
- `poc-hook-input-<timestamp>.json` (A1: file exists; A2: contains `stop_hook_active` field)
- `poc-hook-output-block.json` (A3: first-stop block response logged)
- `poc-hook-output-allow.json` (A4: second-stop allow response logged)"
