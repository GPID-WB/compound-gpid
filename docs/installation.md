# Installation

This page covers installing Compound GPID on a new machine, linking it to a project, and upgrading from an older version.

> **New here?** See the [Home](../README.md) page for an overview of what Compound GPID is and why it exists.

---

> **Choose your install path before Step 1:**
>
> | Environment | Recommended path | Why |
> |-------------|-----------------|-----|
> | Local machine (OneDrive) | `C:\WBG\.compound-gpid` | Avoids Constrained Language Mode issues caused by OneDrive redirecting the Documents folder |
> | Remote server (no OneDrive) | `$env:USERPROFILE\.compound-gpid` | Standard user-profile location; no OneDrive/CLM concerns. **Caveat**: if your username contains spaces or `$env:USERPROFILE` resolves to a UNC path (e.g. `\\server\home\...`), use a local path instead (e.g. `C:\local\.compound-gpid`). |
>
> The scripts are fully location-agnostic — substitute your chosen path in Steps 1 and 2.

## Step 1 — Clone (once per machine)

**Local machine (OneDrive):**
```powershell
git clone https://github.com/GPID-WB/compound-gpid.git "C:\WBG\.compound-gpid"
```

**Remote server (no OneDrive):**
```powershell
git clone https://github.com/GPID-WB/compound-gpid.git "$env:USERPROFILE\.compound-gpid"
```

## Step 2 - Install (once per machine)

**Local machine (OneDrive):**
```powershell
& "C:\WBG\.compound-gpid\install.ps1"
```

**Remote server (no OneDrive):**
```powershell
& "$env:USERPROFILE\.compound-gpid\install.ps1"
```

This creates `cg-link`, `cg-unlink`, and `cg-update` as batch wrappers in the `bin\` subdirectory of your install location and adds that directory to your PATH. It also writes `.cg-version` (set to `latest`) in the install directory so version preference is immediately available.

> ⚠️ **IMPORTANT — After install, restart both your terminal and VS Code / Positron:**
> - **Terminal restart**: the PATH change only takes effect in new processes — `cg-link` will not be found until the terminal is restarted.
> - **VS Code / Positron restart**: Copilot must re-index the workspace to pick up new commands — restart the IDE as well.

> **Execution policy**: if PowerShell blocks the script, run:
> `powershell -ExecutionPolicy Bypass -File "<your-install-path>\install.ps1"`

## Step 3 - Link your project (once per project)

From your project root:

```powershell
cg-link
```

This creates **per-subdirectory junctions** inside `.github/` for the Compound GPID managed directories (`prompts/`, `skills/`, `agents/`, `instructions/`) and **generates** `copilot-instructions.md` from a template, filling in your project name, languages, and review depth. Any existing `.github/` content (GitHub Actions workflows, issue templates, CODEOWNERS, etc.) is preserved untouched.

> ⚠️ **IMPORTANT — Restart VS Code / Positron after linking.**
> Copilot must re-index the workspace to see the newly linked prompts, skills, and agents.
> Without a restart, `/cg-setup` and other prompts will not be available.

> **Developer Mode**: if `cg-link` fails, enable Developer Mode in Windows Settings:
> Settings → System → For developers → Developer Mode → On

> **Managed vs. user-owned files**: files inside the junction directories (`prompts/`, `skills/`, etc.) are managed by Compound GPID - do not edit them directly. `copilot-instructions.md` is regenerated from a template on every `cg-link` and `cg-update` run. To take ownership of the file, remove the `<!-- compound-gpid:managed -->` marker at the top; `cg-update` will then leave your version untouched.

## Step 4 - Configure your project (once per project)

Open your project in VS Code and run in Copilot Chat:

```
/cg-setup
```

> ⚠️ **Do not skip this step.** `/cg-setup` creates the `.cg-docs/` directory structure (brainstorms, plans, reviews, strategy, solutions, archive) required by all workflow prompts. If you skip it, `/cg-strategy`, `/cg-review`, and `/cg-compound` will fail to write their output artifacts.

This configures language preferences, project type, and review depth, scaffolds the `.cg-docs/` directory,
and creates three config files:

- `compound-gpid.local.md` — always created; gitignored; your personal config (language, review depth)
- `compound-gpid.md` — optional; committed; shared project charter (objective, deliverables, constraints, current focus). All `/cg-*` prompts read this automatically.
- `compound-gpid.context.md` — optional; committed; a growing knowledge base for project-specific facts Copilot should know on every task (data sources, variable caveats, workspace folder descriptions, domain vocabulary). All prompts read this in Step 0. Grows over time via `/cg-compound`.

> **Existing repos**: If your project already has code (R, Python, Stata, etc.), `/cg-setup` will dispatch `@cg-project-scanner` to scan the file tree first. The scanner infers language, project type, and a charter draft from existing signals — you only confirm or correct what it found. High-confidence detections are set silently; medium-confidence ones are pre-filled and shown for confirmation. You can skip the charter entirely and create `compound-gpid.md` later by re-running `/cg-setup`.

---

## Updating

From any terminal:

```powershell
cg-update
```

This resets any accidental local changes and then pulls the latest version. Because the managed subdirectories use junctions to the global clone, updates are instantly visible in every linked project - no per-project update step is needed.

---

## Version Pinning

By default `cg-update` tracks `main` and always pulls the latest commit. If you need stability (or want to try a beta), you can pin to a specific [GitHub Release](https://github.com/GPID-WB/compound-gpid/releases).

> **`latest` is a keyword**, not a version number. It means "track `main` and always pull the newest commit" — it does **not** refer to the newest numbered release. To see numbered releases, run `cg-update --list`.

### Browse available releases

```powershell
cg-update --list
```

Fetches the latest tag list and displays it with your current version marked.

### Pin to a specific release

```powershell
cg-update v0.2.0
```

Checks out that release tag and writes `v0.2.0` to `.cg-version` in your install directory. Subsequent bare `cg-update` calls stay on this version.

### Return to tracking main

```powershell
cg-update latest
```

Unpins and resumes pulling `main` on every `cg-update` call.

> **Version preference is per-machine.** It is stored in `.cg-version` inside your global install directory (`C:\WBG\.compound-gpid\.cg-version` or `$env:USERPROFILE\.compound-gpid\.cg-version`). This file is gitignored and never committed — each machine keeps its own preference independently.

> **Full details on version management**: see the dedicated [Version Management](versioning.md) page for command output examples, when to use each mode, multi-machine scenarios, and troubleshooting.

---

## Repairing a broken installation

If `cg-update` fails (e.g. untracked files blocking `git pull`, or local changes in the global clone), use the built-in repair command:

```powershell
cg-update --fix
```

This cleans untracked files, discards local changes, and pulls the latest code.

**If `cg-update --fix` itself fails** (e.g. the installed copy is too old to have `--fix`), run the equivalent commands manually:

```powershell
# Uncomment your install path:
$cg = "C:\WBG\.compound-gpid"              # local machine (OneDrive)
# $cg = "$env:USERPROFILE\.compound-gpid"    # remote server
git -C $cg clean -fd
git -C $cg checkout .
git -C $cg pull --ff-only
```

Then run `cg-update` from each linked project to apply any structural migrations.

> **Existing projects — `.cg-docs/strategy/`**: If you linked your project before this release, create the strategy folder manually:
> ```powershell
> New-Item -ItemType Directory -Force .cg-docs\strategy | Out-Null
> New-Item -ItemType File -Force .cg-docs\strategy\.gitkeep | Out-Null
> ```

> **Migrating from an old install path?** If you previously installed to `$env:USERPROFILE\.compound-gpid` on a local OneDrive machine, see [Upgrading from an old installation](troubleshooting.md#upgrading-from-envuserprofilecompound-gpid-old-default-path--local-onedrive-machines-only) in the Troubleshooting page.

---

> **Having trouble?** Check the [Troubleshooting](troubleshooting.md) page for known issues and fixes.

