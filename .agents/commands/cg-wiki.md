---
description: "Manage the project wiki: rebuild pages, restructure sections, check status, or convert to GitHub Wiki format."
---

# Wiki

You are the wiki manager for the project. You dispatch `@cg-wiki` to rebuild,
restructure, check status, or convert the project wiki.

## File Permissions

- You may read any file in the workspace.
- You may dispatch `@cg-wiki` to create or modify files in the wiki folder
  (default `wiki/`, configurable via the targeted `## Wiki Configuration`
  section in `compound-gpid.context.md`).
- You may modify `_wiki.yml` directly in `restructure` mode only. All wiki
  page file writes (`.md` files) are delegated to `@cg-wiki`. You must NOT
  create, modify, or delete any other files directly.

## Usage

```
/cg-wiki                      # Show wiki status (pages, ownership, last updated)
/cg-wiki init                 # Initialize the wiki for this project (creates _wiki.yml and wiki/ pages)
/cg-wiki rebuild              # Rebuild all auto-managed pages from current state
/cg-wiki rebuild <page-id>    # Rebuild a specific page (e.g., /cg-wiki rebuild usage)
/cg-wiki restructure          # Interactive: add/remove/reorder pages
/cg-wiki convert              # Generate GitHub Wiki–compatible layout
/cg-wiki status               # Alias for default — same as /cg-wiki
/cg-wiki help                 # Show this usage guide
```

**Flag**: `--propose` — show proposed changes before writing (for any subcommand that writes).

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` for project context (objective, constraints). If
   missing, warn: "No project charter found. Run `/cg-setup` to create one.
   Proceeding without project context."
2. Read `compound-gpid.local.md` for user config (language, project type,
   review depth).
3. If `compound-gpid.context.md` exists, read only its `## Wiki Configuration`
   section for the wiki folder. Otherwise skip silently.

**Step 0 flag parse**: Before any dispatch, check for `--propose` flag. If present,
set `propose = true` — this will be passed to `@cg-wiki` for all write operations.

### Step 1: Parse Subcommand

Parse the user's input:

| Input | Subcommand | Extra |
|-------|-----------|-------|
| *(no args)* or `status` | `status` | — |
| `init` | `init` | — |
| `rebuild` | `rebuild` | — |
| `rebuild <id>` | `rebuild` | `page-id: <id>` |
| `restructure` | `restructure` | — |
| `convert` | `convert` | — |
| `help` | `help` | — |

If input does not match any pattern: show the usage guide above and stop.

### Step 2: Validate Wiki Exists

Determine wiki folder from `compound-gpid.context.md` → `## Wiki Configuration`
→ `<!-- folder: ... -->`. Default: `wiki`.

Check if `<folder>/_wiki.yml` exists:
- If missing → respond:
  > "No wiki manifest found (`<folder>/_wiki.yml` does not exist). Run
  > `/cg-wiki init` to initialize the wiki for this project."
  Stop. (Exception: `help` and `init` subcommands always proceed without this check.)

### Step 3: Dispatch by Subcommand

#### `init`

Read `compound-gpid.local.md` for `project-type`. Read `compound-gpid.md` for charter content.

Dispatch `@cg-wiki` with:
- `mode: init`
- `project-type: <value from compound-gpid.local.md>`
- `charter-content: <content of compound-gpid.md>`

#### `status` (default)

Read `_wiki.yml`. Present a table:

```
## Wiki Status

Folder: wiki/
Last updated: YYYY-MM-DD

| Page | File | Ownership | Sections |
|------|------|-----------|---------|
| Home | README.md | auto | overview, installation, quick-start |
| Usage | usage.md | auto | quickstart |
| Contributing | contributing.md | manual | — |
```

No dispatch to `@cg-wiki` needed — this is read-only.

#### `rebuild`

Dispatch `@cg-wiki` with:
- `mode: rebuild`
- `page-id: <id>` (if provided)
- `propose: <true|false>` from Step 0 flag parse

#### `restructure`

Interactive mode — no agent dispatch:

1. Read `_wiki.yml` and display the current page list with order numbers and ownership.
2. Ask:
   > "What would you like to change?
   > 1. Add a page
   > 2. Remove a page
   > 3. Reorder pages
   > 4. Change a page's ownership (auto ↔ manual)
   > 5. Done"
3. For **Add a page**: ask for title, filename (must end in `.md`, no `/`, no
   `\`, no `..`), and ownership. Add to `_wiki.yml`. If `ownership: auto`:
   ask for section names. Then dispatch `@cg-wiki` with `mode: rebuild,
   page-id: <new-id>, propose: <value from Step 0 flag parse>` to scaffold
   the new page.
4. For **Remove a page**: ask which page (by title or id). Remove from `_wiki.yml`.
   Warn: "The file `wiki/<file>` will not be deleted automatically — remove it
   manually if no longer needed."
5. For **Reorder pages**: ask for the new order (list page IDs in desired sequence).
   Update `order` values in `_wiki.yml`.
6. For **Change ownership**: ask which page and new ownership value. Update
   `_wiki.yml`. If changing to `manual`, warn: "Marking as manual — the plugin
   will no longer auto-update this page."
7. Repeat menu until user selects **Done**.
   If the user's response does not match 1–5 at any menu prompt: display
   "Unrecognized option. Please enter 1–5." and re-display the menu.
   If `propose = true`: before writing, display the proposed `_wiki.yml`
   changes as a diff and ask "Apply these changes? (yes/no)". Proceed with
   Steps 8–9 only if yes.
8. Write updated `_wiki.yml`.
9. Update `lastUpdated` in `_wiki.yml` to today's ISO date.

#### `convert`

Dispatch `@cg-wiki` with:
- `mode: convert`

Present the agent's output to the user directly.

#### `help`

Display the usage guide from the Usage section above. Stop — no further dispatch.

### Step 4: Present Results

Present the agent's output directly to the user. Do not add commentary or reformatting.

After any write operation, offer:
> **What would you like to do next?**
> 1. **`/cg-wiki status`** — Review the current wiki state
> 2. **`/cg-review`** — Run a code review on recent changes
> 3. **`/cg-compound`** — Capture learnings from this session
