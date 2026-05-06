---
date: 2026-05-05
title: "print_yellow inside command substitution corrupts captured variable with ANSI text"
category: "bugs"
language: "bash"
tags: [bash, command-substitution, stdout, stderr, ansi-escape, shell-profile, detect_profile, print_yellow, silent-failure]
root-cause: "A helper function called via command substitution wrote user-facing warnings to stdout instead of stderr. The warning text was captured into the assignment variable alongside the intended return value, producing a multi-line ANSI-escape-polluted string that silently failed all downstream file operations."
severity: "P1"
---

# `print_yellow` inside command substitution corrupts captured variable with ANSI text

## Problem

`scripts/install.sh` added a warning branch to `detect_profile()` for unrecognized shells (fish, nushell, tcsh) as part of a P3.8 fix. The warning used `print_yellow`, a helper defined as:

```bash
print_yellow() { printf '\033[0;33m%s\033[0m\n' "$1"; }
```

The function is called via command substitution:

```bash
PROFILE_FILE="$(detect_profile)"
```

For any unrecognized shell, `PROFILE_FILE` received the concatenated stdout of the entire function:

```
\033[0;33mWarning: unrecognized shell 'fish'. Defaulting to ~/.bashrc.\033[0m
  You may need to manually add the PATH block to your shell profile.
/home/user/.bashrc
```

Every subsequent use of `$PROFILE_FILE` silently failed:
- `grep -qF "$CG_PROFILE_START" "$PROFILE_FILE"` — no error, no match
- `>> "$PROFILE_FILE"` — created a junk file with the ANSI-escape string as its name
- The PATH block was never written to the real shell profile

The install appeared to succeed (exit code 0, success message printed) but had no effect for any user not on zsh or bash.

## Root Cause

`print_yellow` writes to **stdout** (the default for `printf`). When the enclosing function is invoked inside `$(...)`, all stdout is captured into the assignment variable. The return value of a bash function is its last stdout line — preceding stdout lines are also captured, not discarded.

The fix author assumed `print_yellow` was stderr-safe because it looks like a display helper. It is not — it lacks `>&2`.

This is a latent trap in any bash codebase that uses `printf`-based color helpers without stderr redirection: the helper works correctly when called at the top level but silently corrupts any function that uses it and is then called via command substitution.

## Solution

Redirect all non-return stdout inside functions that are used via command substitution to `>&2`:

```bash
detect_profile() {
    local shell_name
    shell_name="$(basename "${SHELL:-/bin/zsh}")"
    if [[ "$shell_name" == "zsh" ]]; then
        echo "$HOME/.zshrc"
    elif [[ "$shell_name" == "bash" ]]; then
        echo "$HOME/.bashrc"
    else
        print_yellow "Warning: unrecognized shell '$shell_name'. Defaulting to ~/.bashrc." >&2
        print_yellow "  You may need to manually add the PATH block to your shell profile." >&2
        echo "$HOME/.bashrc"
    fi
}
```

The `>&2` redirects are on the `print_yellow` calls specifically, not on the function as a whole. `echo "$HOME/.bashrc"` remains on stdout and is correctly captured by the caller.

## Prevention

### Rule: Functions used via command substitution must be stdout-clean

Any bash function whose return value is captured via `$(fn)` must write **only** the return value to stdout. All diagnostic output (warnings, progress messages, debug info) must go to `>&2`.

**Anti-pattern** (corrupts the captured variable):
```bash
my_helper() {
    print_yellow "Warning: ..." # ← stdout — will be captured!
    echo "/the/path"
}
RESULT="$(my_helper)"  # RESULT = warning text + "/the/path"
```

**Correct pattern**:
```bash
my_helper() {
    print_yellow "Warning: ..." >&2  # ← stderr — not captured
    echo "/the/path"                 # ← stdout — captured correctly
}
RESULT="$(my_helper)"  # RESULT = "/the/path" only
```

### Naming convention hint

Consider naming stdout-capturing functions with a `get_` prefix and display-only functions with `print_`/`show_` to signal intent. Any function called as `VAR="$(fn)"` must be treated as stdout-clean.

### Verify mode catches this

This regression was introduced by a P3 fix and surfaced by `mode:verify` in the next review cycle. The verify pass caught it as a P1 despite the original review rating the fix as P3 — proof that `mode:verify` is essential after fix-triage even for low-priority findings.

## Related

- `.cg-docs/solutions/bugs/2026-03-19-persistent-state-written-before-validation-causes-corruption.md` — similar theme: a "safe" helper operation silently corrupts persistent state. Both cases share the pattern of a function that looks harmless (print a message / write a version) causing silent downstream failures.
