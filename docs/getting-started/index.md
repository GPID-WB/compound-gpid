# Getting Started

Use this path to understand Compound GPID, install it, configure one project,
and complete a first useful workflow. The normal setup provides generated
targets for GitHub Copilot, Claude Code, Codex, OpenCode, and Kilo from one canonical
plugin source.

## 1. Confirm the fit

Compound GPID is for data science and software work that benefits from explicit
planning, risk-based review, reproducible evidence, and durable project
knowledge. It includes dedicated guidance for R, Python, Stata, analytical and
statistical work, testing, visualization, and institutional writing.

Read [Working with AI Responsibly](../philosophy.md) for the philosophy behind
responsible use, then read [Why Compound GPID?](../why-compound-gpid.md) for its
relationship to the Compound Engineering plugin and the tradeoffs introduced by
institutional operating constraints.

## 2. Install once per machine

Requirements are Git, Python 3.8 or later, and a supported agent host. Windows
also requires PowerShell 5.1 or later.

### Windows

On a World Bank-managed local machine with OneDrive, the documented default
avoids the redirected Documents folder:

```powershell
git clone https://github.com/GPID-WB/compound-gpid.git "C:\WBG\.compound-gpid"
& "C:\WBG\.compound-gpid\install.ps1"
```

For a remote server without OneDrive, use
`$env:USERPROFILE\.compound-gpid`. Restart the terminal and IDE after install.

### macOS

```bash
git clone https://github.com/GPID-WB/compound-gpid.git ~/.compound-gpid
bash ~/.compound-gpid/scripts/install.sh
```

Restart the terminal and IDE after install. Linux uses the same shell scripts,
although the detailed installation guide currently states tested macOS
requirements rather than a separate Linux support matrix.

See [Installation Details](../installation.md) for path selection, Python
detection, execution policy, repair, migration, and uninstall procedures.

## 3. Link one project

Run from the project root:

```bash
cg-link
```

By default, this links managed install units for all five supported platforms.
To narrow the install, provide a comma-separated platform list:

```bash
cg-link --platforms copilot,opencode,kilo
```

Existing user-owned platform files are preserved. Compound GPID skips a
conflicting unit and reports what needs manual attention rather than replacing
the file silently. Restart the IDE after linking.

## 4. Configure the project

In the agent chat, run:

```text
/cg-setup
```

Confirm the project language, R dialect when applicable, project type, review
depth, and active suites. Choose `suites: [cg]` for technical workflows,
`suites: [cr]` for research workflows, or `suites: [cg, cr]` for both. Setup
creates the required `.cg-docs/` structure and may create:

- `compound-gpid.local.md`: committed team settings, including active suites.
- `compound-gpid.md`: optional committed project charter.
- `compound-gpid.context.md`: optional committed project knowledge.

Do not skip setup. Workflow prompts depend on the `.cg-docs/` structure it
creates. See [Configuration](../configuration/index.md) before changing managed
or shared files manually.

## 5. Complete a first workflow

Choose a small real task whose expected result can be checked. Technical work
uses the `/cg-*` loop:

```text
/cg-brainstorm
/cg-plan
/cg-work
/cg-review light
/cg-fix-triage
/cg-compound
```

Research work uses the parallel `/cr-*` loop, with research integrity,
provenance, method, and publication checks owned by that suite:

```text
/cr-brainstorm
/cr-plan
/cr-work
/cr-review
/cr-compound
```

For the research-first onboarding path, continue with the [Research Handbook](../research/index.md).

Use `/cg-plan-review` between planning and work when the task is consequential
or the plan depends on uncertain assumptions. For an already well-defined,
small task, start at `/cg-plan`; for a reproducible bug, use `/cg-fixbug`.

The useful outcome is not merely a chat response. Check that the code or
document changed as intended, validation evidence exists, review findings were
resolved or explicitly deferred, and a reusable lesson was captured only after
verification.

## Next pages

- [Workflow Overview](../workflows/index.md) selects a route by task.
- [Research Handbook](../research/index.md) guides a first research workflow.
- [Modular Guide](../modular-guide.md) explains suite selection and composition.
- [Skills Catalog](../skills/index.md) shows the analytical and technical guidance available.
- [Governance and Security](../governance/index.md) explains constraints and limitations.
- [Help and Troubleshooting](../help/index.md) provides safe recovery paths.
