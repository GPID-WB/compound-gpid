## PR Checklist

Please verify each dimension before requesting review. For each item, check
the box **or** add a brief note explaining why it is N/A.

- [ ] **E2E verified** — I ran `cg-link` / `cg-unlink` on a fresh project
  directory locally on my platform. On Windows, junctions were created in
  `.github/`. On macOS/Linux, symlinks were created. `cg-setup.prompt.md` was
  accessible through the link. If the change does not touch `link.*` or
  `unlink.*`, this is N/A.

- [ ] **Tests added / updated** — New behaviour is covered by tests. Existing
  tests pass. If no code changed (e.g., docs-only PR), state N/A.

- [ ] **Cross-script parity** — Changes to `.ps1` scripts are mirrored in
  the `.sh` equivalents (and vice versa). The managed directories list,
  verification file path, and `.gitignore` block marker are identical across
  the pair. The `parity` CI check passes. If the change is documentation-only
  or touches only one platform script intentionally, explain here.

- [ ] **Docs updated** — `docs/installation.md`, `docs/manual.md`, or
  `README.md` reflect any behavioral changes. N/A if no user-facing behavior
  changed (e.g., internal refactor, test-only change, CI change).

- [ ] **Backward compatible** — Users with existing installs (junctions or
  symlinks created by a prior version) can run `cg-update` and then `cg-link`
  without errors. Tested or reasoned-about explicitly.

- [ ] **Idempotent** — Running the changed command twice in a row on the same
  project directory produces no errors, no duplicate entries, no extra files.
  The E2E smoke test checks this automatically, but note any edge cases here.

- [ ] **Commit conventions** — All commits follow `type(scope): description`
  format. Allowed types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`,
  `data`, `analysis`. The PR title (used as the squash-merge commit message)
  also follows this format.

- [ ] **Security reviewed** — Path handling does not introduce directory
  traversal vulnerabilities or symlink-following attacks. No user-controlled
  input flows into path construction without validation. Junction / symlink
  cleanup uses the safe 2-level scan pattern (no `Remove-Item -Recurse` on
  trees that may contain junctions).

---

**Description**

<!-- What does this PR change and why? -->

**Related issues / PRs**

<!-- Closes #NNN or References #NNN -->
