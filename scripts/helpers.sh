#!/usr/bin/env bash
# scripts/helpers.sh
# Shared shell helper functions sourced by link.sh and update.sh.
#
# DO NOT add set -euo pipefail here — this file is sourced, not executed
# directly. Error handling and colour helpers (print_error, etc.) are
# provided by the calling script before sourcing.

# ---------------------------------------------------------------------------
# generate_copilot_instructions <template_path> <project_root> <marker>
# Reads the template, parses frontmatter from compound-gpid.md and
# compound-gpid.local.md, substitutes placeholders, and writes the result
# (with management marker prepended) to stdout.
# ---------------------------------------------------------------------------
generate_copilot_instructions() {
    local template_path="$1"
    local project_root="$2"
    local marker="$3"

    python3 - "$template_path" "$project_root" "$marker" <<'PYEOF' || { print_error "Failed to generate copilot-instructions.md from template."; exit 1; }
import sys, re, os

template_path, project_root, marker = sys.argv[1], sys.argv[2], sys.argv[3]

charter_path = os.path.join(project_root, 'compound-gpid.md')
local_path   = os.path.join(project_root, 'compound-gpid.local.md')

def extract_fm_value(path, key):
    """Extract a YAML frontmatter value by key. Returns '' if not found."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        m = re.match(r'^---[ \t]*\n(.*?)\n---', content, re.DOTALL)
        if not m:
            return ''
        fm = m.group(1)
        # Use \x27 for single-quote and \r\n for line terminators to avoid
        # raw-string double-backslash confusion (r'\\r' = literal \r not CR).
        pattern = r'(?m)^\s*' + re.escape(key) + r':\s*["\x27]?([^"\x27\r\n]+)["\x27]?\s*$'
        vm = re.search(pattern, fm)
        return vm.group(1).strip() if vm else ''
    except Exception:
        return ''

# Read project-name from charter
project_name = extract_fm_value(charter_path, 'project-name') or '<project-name>'

# Read per-user config from compound-gpid.local.md
language     = extract_fm_value(local_path, 'language')     or '<not configured>'
project_type = extract_fm_value(local_path, 'project-type') or '<not configured>'
review_depth = extract_fm_value(local_path, 'review-depth') or '<not configured>'
modules      = extract_fm_value(local_path, 'modules')      or 'engineering'

# Validate modules: field — reject YAML list notation and unrecognised values
if modules.startswith('['):
    print('ERROR: Invalid modules format in compound-gpid.local.md: YAML list notation is not '
          'supported. Use a quoted string: modules: "engineering, research"', file=sys.stderr)
    sys.exit(1)
VALID_MODULES = {'engineering', 'research', 'engineering, research', 'research, engineering'}
if modules not in VALID_MODULES:
    print(f'ERROR: Invalid modules value "{modules}" in compound-gpid.local.md. '
          f'Valid values: {", ".join(sorted(VALID_MODULES))}', file=sys.stderr)
    sys.exit(1)

r_syntax     = extract_fm_value(local_path, 'r-syntax')

# Build languages string — append R dialect when configured
languages = language
if r_syntax and re.search(r'\bR\b', language, re.IGNORECASE):
    languages = f'{language} (R dialect: {r_syntax})'

# Guard: reject config values that contain placeholder tokens
for val in (project_name, project_type, languages, review_depth, modules):
    if '{{' in val:
        print('ERROR: A config value contains a placeholder token which would corrupt the output.'
              ' Check compound-gpid.md and compound-gpid.local.md.', file=sys.stderr)
        sys.exit(1)

# Read template
with open(template_path, 'r', encoding='utf-8') as f:
    template = f.read()

if not template.strip():
    print(f'ERROR: Template file is empty: {template_path}. Run cg-update --fix.', file=sys.stderr)
    sys.exit(1)

# Substitute placeholders (literal, not regex — mirrors PS .Replace() behaviour)
output = template
output = output.replace('{{project-name}}', project_name)
output = output.replace('{{project-type}}', project_type)
output = output.replace('{{languages}}',    languages)
output = output.replace('{{review-depth}}', review_depth)
output = output.replace('{{modules}}',      modules)

# Prepend the management marker, matching the template's line-ending style
sep = '\r\n' if '\r\n' in output else '\n'
sys.stdout.write(marker + sep + output)
PYEOF
}
