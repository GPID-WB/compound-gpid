# Installation

This detailed page covers platform-specific installation, linking, repair, and
uninstall procedures. New users should follow the shorter
[Getting Started](getting-started/index.md) path first.

> **New here?** See the [Home](../README.md) page for an overview of what Compound GPID is and why it exists.

**Platform**: Jump to your operating system:
- [Windows installation](#windows-installation)
- [macOS installation](#macos-installation)

---

## Windows installation

> **Requirements**: Windows 10/11, PowerShell 5.1+, git, **Python 3.8+**.
> Python is required by `cg-skill`, the `cg-index` knowledge indexer, the `cg-token-audit` context/model audit, and the repo-local summary tools. Install from [python.org](https://www.python.org/downloads/) or via winget: `winget install Python.Python.3.11`. The Windows Store Python stub is not sufficient — install real Python and ensure `python`, `python3`, or `py` is on your PATH. If Python is not installed, `install.ps1` will stop with an error and print install instructions. See [Python not found](troubleshooting.md#python-not-found) in Troubleshooting if you run into issues.
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

This creates batch wrappers for `cg-link`, `cg-unlink`, `cg-update`, `cg-skill`, `cg-index`, `cg-brain-init`, `cg-render-artifact`, `cg-publish-markdown`, and `cg-token-audit` in the `bin\` subdirectory of your install location and adds that directory to your PATH. Python 3.8+ powers the skill lifecycle, Brainstorm/Plan validation, and HTML rendering through `cg-render-artifact`, plus secure generic Markdown publication through `cg-publish-markdown` with the `reference` theme. It also writes `.cg-version` (set to `latest`) in the install directory so version preference is immediately available. The `cg-index query` mode provides budgeted local Brain retrieval; `cg-token-audit` writes both legacy `.cg-docs/cost/` reports and additive `.cg-docs/token/` dashboard/regression artifacts.

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

This links Compound GPID install units for all supported platforms by default: GitHub Copilot (`.github/`), Claude Code (`.claude/`), Codex (`.agents/`), OpenCode (`.opencode/`), and Kilo (`.kilo/`). Kilo runtime directories are project-local managed copies; other directory units are junctions on Windows. Strict config/root-adapter files are copied only when managed by Compound GPID, so existing user-owned files are preserved.

> **Platform selection**: To install only specific platforms, pass `--platforms`:
> ```powershell
> cg-link --platforms copilot
> cg-link --platforms kilo
> cg-link --platforms copilot,claude-code,codex,opencode,kilo
> ```
> Default (`cg-link` with no flag) links all supported platforms. See [Context
> Files](context-files.md) for details on generated native platform trees.

> **Kilo + Codex/Claude coexistence**: when a project contains Kilo plus a
> Codex or Claude skill root, direct Kilo editor/CLI launches are unsupported.
> Run the certified launcher `cg-kilo` from the project root. It performs the
> local projection and supported-host preflight, then sets
> `KILO_DISABLE_EXTERNAL_SKILLS=1` only for the child Kilo process. It does not
> modify global Kilo configuration or the caller's environment. If the host
> version, local projection, or containment check is unsupported, `cg-link` and
> `cg-update` fail with remediation rather than claiming coexistence support.

> ⚠️ **IMPORTANT — Restart VS Code / Positron after linking.**
> Copilot must re-index the workspace to see the newly linked prompts, skills, and agents.
> Without a restart, `/cg-setup` and other prompts will not be available.

> **Developer Mode**: if `cg-link` fails, enable Developer Mode in Windows Settings:
> Settings → System → For developers → Developer Mode → On

> **Managed vs. user-owned files**: files inside linked directories (`prompts/`, `skills/`, `commands/`, `agents/`, etc.) are managed by Compound GPID - do not edit them directly. `copilot-instructions.md` is regenerated from a template on every `cg-link` and `cg-update` run while the `<!-- compound-gpid:managed -->` marker is present. Strict JSON config files such as `.opencode/opencode.json` use `.compound-gpid/managed-files.json` checksums instead of inline markers; `cg-update` refreshes them only if they are unmodified. If a user-owned config exists, `cg-link` skips it and prints a manual snippet.
>
> The consumer `.compound-gpid/managed-files.json` is separate from the
> `.compound-gpid-generated.json` manifests committed inside the upstream
> `.claude/`, `.agents/`, `.opencode/`, and `.kilo/` trees. Consumers should not
> copy, edit, or use generated-tree manifests to resolve installation ownership.

## Step 4 - Configure your project (once per project)

Open your project in VS Code and run in Copilot Chat:

```
/cg-setup
```

> ⚠️ **Do not skip this step.** `/cg-setup` creates the `.cg-docs/` directory structure (brainstorms, plans, reviews, strategy, solutions, archive) required by all workflow prompts. If you skip it, `/cg-strategy`, `/cg-review`, and `/cg-compound` will fail to write their output artifacts.

This configures language preferences, project type, review depth, and active
suites, scaffolds the `.cg-docs/` directory,
and creates three config files:

- `compound-gpid.local.md` — always created and committed; shared team config (language, review depth, and `suites: [cg]`, `[cr]`, or `[cg, cr]`)
- `compound-gpid.md` — optional; committed; shared project charter (objective, deliverables, constraints, current focus). All `/cg-*` prompts read this automatically.
- `compound-gpid.context.md` — optional; committed; a growing knowledge base for project-specific facts Copilot can consult when needed (data sources, variable caveats, workspace folder descriptions, domain vocabulary). Ordinary prompts load targeted headings or snippets instead of reading the whole file by default. Grows over time via `/cg-compound`.

> **Existing repos**: If your project already has code (R, Python, Stata, etc.), `/cg-setup` will dispatch `@cg-project-scanner` to scan the file tree first. The scanner infers language, project type, and a charter draft from existing signals — you only confirm or correct what it found. High-confidence detections are set silently; medium-confidence ones are pre-filled and shown for confirmation. You can skip the charter entirely and create `compound-gpid.md` later by re-running `/cg-setup`.

> **Claude Code / Codex / OpenCode / Kilo support**: Compound GPID generates native
> platform trees (`.claude/`, `.agents/`, `.opencode/`, `.kilo/`) from the
> canonical `.github/` source. `cg-link` links them by default; pass `--platforms`
> to narrow the target set. The legacy `adapters/` directory contains
> opt-in source adapters that are superseded by the generated trees but remain
> for backward compatibility.
>
> Each linked skill is an atomic bundle: `SKILL.md` and all nested regular
> support files are included by default. Executable resources are opaque files;
> packaging preserves their mode but never executes them. See
> [Generated Native Platform Trees](context-files.md#generated-native-platform-trees).

> **Kilo parser diagnostics**: malformed managed Kilo skill, agent, and `cg-*`
> command frontmatter is reported as a local-content failure. Kilo's own
> schema-validation failure is reported separately from external skill
> discovery; one must not be used as evidence for the other.

> **Suite selection**: `/cg-setup` records active suites in
> `compound-gpid.local.md`. An absent `suites:` field defaults to `[cg]` for
> backward compatibility. Linked projects share the global all-suite native
> target baseline; `suites:` controls workflow eligibility and instruction-level
> loading for that project. Maintainers can request an isolated filtered build
> with `--active-suites`. See the [Modular Guide](modular-guide.md).

---

## macOS installation

> **Requirements**: macOS 12 (Monterey) or later, bash (pre-installed), git, **Python 3.8+**.
> macOS often provides `python3` through Xcode Command Line Tools. Compound GPID probes `python3`, then `python`, then `py` and accepts the first command whose `--version` output starts with `Python`. If none is on your PATH, run `xcode-select --install` or install Python from python.org/Homebrew.

### Step 1 — Clone (once per machine)

```bash
git clone https://github.com/GPID-WB/compound-gpid.git ~/.compound-gpid
```

You can substitute any path you prefer, e.g. `~/tools/.compound-gpid`. The scripts are fully location-agnostic.

### Step 2 — Install (once per machine)

```bash
bash ~/.compound-gpid/scripts/install.sh
```

This:
- Creates or refreshes bash wrappers (`cg-link`, `cg-unlink`, `cg-update`, `cg-skill`, `cg-index`, `cg-brain-init`, `cg-render-artifact`, `cg-publish-markdown`, `cg-token-audit`) in `~/.compound-gpid/bin/`; Python 3.8+ provides skill lifecycle management, Brainstorm/Plan validation, HTML rendering, and generic Markdown publication with the `reference` theme, and the same `bin/` directory also contains repo-local summary wrappers such as `cg-test-summary`, `cg-diff-summary`, `cg-log-summary`, `cg-tree-summary`, and `cg-problems-summary`
- Adds that directory to your PATH via `~/.zshrc` (or `~/.bashrc` for bash users)
- Writes `.cg-version` (set to `latest`) in the install directory

> ⚠️ **IMPORTANT — After install, restart your terminal and VS Code / Positron:**
> - **Terminal restart**: the PATH change only takes effect in new processes.
> - **VS Code / Positron restart**: Copilot must re-index the workspace to pick up new commands.

### Step 3 — Link your project (once per project)

From your project root:

```bash
cg-link
```

This links Compound GPID install units for all supported platforms by default: GitHub Copilot (`.github/`), Claude Code (`.claude/`), Codex (`.agents/`), OpenCode (`.opencode/`), and Kilo (`.kilo/`). Kilo runtime directories are project-local managed copies; other directory units are symlinks on macOS. Strict config/root-adapter files are copied only when managed by Compound GPID, so existing user-owned files are preserved.

> **Platform selection**: To install only specific platforms:
> ```bash
> cg-link --platforms copilot
> cg-link --platforms kilo
> cg-link --platforms copilot,claude-code,codex,opencode,kilo
> ```
> Default (`cg-link` with no flag) links all supported platforms.

> With Kilo and Codex/Claude roots present, launch Kilo only through
> `cg-kilo`. The certified launcher is the supported containment boundary;
> direct editor/CLI launches are intentionally unsupported by the coexistence
> policy.

> ⚠️ **IMPORTANT — Restart VS Code / Positron after linking.**
> Copilot must re-index the workspace to see the newly linked prompts, skills, and agents.

The legacy `adapters/` directory contains opt-in source adapters that are
superseded by the generated native trees but remain for backward compatibility.

### Step 4 — Configure your project (once per project)

Open your project in VS Code and run in Copilot Chat:
```
/cg-setup
```

> ⚠️ **Do not skip this step.** `/cg-setup` creates the `.cg-docs/` directory structure (brainstorms, plans, reviews, strategy, solutions, archive) required by all workflow prompts. If you skip it, `/cg-strategy`, `/cg-review`, and `/cg-compound` will fail to write their output artifacts.

### macOS — Updating

```bash
cg-update
```

This resets any accidental local changes and then pulls the latest version. Linked directory units update instantly through symlinks/junctions. Copied managed files in the current project are refreshed through `.compound-gpid/managed-files.json` only when their checksum still matches the managed copy.

**Version pinning**: the same pinning commands work on macOS:

```bash
cg-update --list       # browse available releases
cg-update v0.2.0      # pin to a specific release
cg-update latest      # return to tracking main
```

Version preference is stored in `~/.compound-gpid/.cg-version` (or your chosen install path). See [Version Management](versioning.md) for full details.

## Uninstalling

### Windows - Uninstalling

```powershell
& "C:\WBG\.compound-gpid\install.ps1" -Uninstall
# remote-server install: & "$env:USERPROFILE\.compound-gpid\install.ps1" -Uninstall
```

This removes the PATH registry entry and legacy profile functions while preserving package-owned `bin\cg-*` wrapper sources for reinstall. The install directory itself is not deleted — remove it manually if desired:

```powershell
Remove-Item -LiteralPath "C:\WBG\.compound-gpid" -Recurse -Force
```

Restart VS Code / Positron and your terminal after uninstalling.

### macOS - Uninstalling

```bash
bash <your-install-path>/scripts/install.sh --uninstall
# e.g. bash ~/.compound-gpid/scripts/install.sh --uninstall
```

This removes the PATH block from your shell profile while preserving package-owned `bin/cg-*` wrapper sources for reinstall. The install directory itself is not deleted — remove it manually if desired.

---

## Updating

**Windows** (from any terminal):
```powershell
cg-update
```

**macOS** (from any terminal):
```bash
cg-update
```

This resets any accidental local changes and then pulls the latest version. Linked directory units update instantly through symlinks/junctions. Copied managed files in the current project are refreshed through `.compound-gpid/managed-files.json` only when their checksum still matches the managed copy.

### Refreshing existing consumer projects

The root `.compound-gpid-source.json` marker belongs only to the Compound GPID
source checkout. It is not projected or installed in consumer projects.

- **Legacy links**: run `cg-update`. Existing directory links receive the fixed
  command immediately. Run `cg-link --platforms <platforms>` only to recreate or
  repair old links.
- **Kilo managed copies**: run `cg-update` from the consumer project so managed
  `.kilo/` files refresh. If the project predates managed-file tracking, run
  `cg-link --platforms kilo` once after the update.
- **Manifest projections**: run `cg-update` to refresh checksum-owned projected
  files. Rerun `cg-link --platforms <platforms>` after a platform-selection or
  install-unit change.

Restart VS Code or Positron after a refresh so the host reloads command files.

---

## Version Pinning

By default `cg-update` tracks `main` and always pulls the latest commit. If you need stability (or want to try a beta), you can pin to a specific [GitHub Release](https://github.com/GPID-WB/compound-gpid/releases).

> **`latest` is a keyword**, not a version number. It means "track `main` and always pull the newest commit" — it does **not** refer to the newest numbered release. To see numbered releases, run `cg-update --list`.

### Browse available releases

```bash
cg-update --list
```

Fetches the latest tag list and displays it with your current version marked.

### Pin to a specific release

```bash
cg-update v0.2.0
```

Checks out that release tag and writes `v0.2.0` to `.cg-version` in your install directory. Subsequent bare `cg-update` calls stay on this version.

### Return to tracking main

```bash
cg-update latest
```

Unpins and resumes pulling `main` on every `cg-update` call.

> **Version preference is per-machine.** It is stored in `.cg-version` inside your global install directory:
> - **Windows**: `C:\WBG\.compound-gpid\.cg-version` or `$env:USERPROFILE\.compound-gpid\.cg-version`
> - **macOS**: `~/.compound-gpid/.cg-version` (or your chosen install path)
>
> This file is gitignored and never committed — each machine keeps its own preference independently.

> **Full details on version management**: see the dedicated [Version Management](versioning.md) page for command output examples, when to use each mode, multi-machine scenarios, and troubleshooting.

---

## Repairing a broken installation

If `cg-update` fails (e.g. untracked files blocking `git pull`, or local changes in the global clone), use the built-in repair command:

```bash
# macOS
cg-update --fix
```
```powershell
# Windows
cg-update --fix
```

This cleans untracked files, discards local changes, and pulls the latest code.

**If `cg-update --fix` itself fails** (e.g. the installed copy is too old), run the equivalent commands manually:

**macOS:**
```bash
cg="$HOME/.compound-gpid"   # adjust if you chose a different install path
git -C "$cg" clean -fd
git -C "$cg" checkout .
git -C "$cg" pull --ff-only
```

**Windows:**
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

> **Migrating from an old install path?** If you previously installed to `$env:USERPROFILE\.compound-gpid` on a local OneDrive machine, see [Upgrading from an old installation](troubleshooting.md#upgrading-from-envuserprofilecompound-gpid-old-default-path-local-onedrive-machines-only) in the Troubleshooting page.

---

> **Having trouble?** Check the [Troubleshooting](troubleshooting.md) page for known issues and fixes.
