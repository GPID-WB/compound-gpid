#!/usr/bin/env bash
# Host matrix, command-line part (issue #211).
#
# Run by the maintainer, in a terminal, from the repository root:
#     bash spike/host-matrix/run_cli_checks.sh
#
# It starts the Claude Code, Codex and Kilo command-line programs that the
# editor extensions bundle, sends each the same four prompts, and saves what
# they answer. It installs two test skills for the run and removes them at the
# end. It changes nothing else. Expect a few minutes and a small token cost on
# each account.
#
# Options, as environment variables:
#     ONLY=kilo                      run one program: claude, codex or kilo
#     KILO_MODEL=provider/model      model for Kilo; its default may not support tools.
#                                    The provider decides who pays: kilo/... needs credits on
#                                    the Kilo account; openai/... and github-copilot/... use the
#                                    account signed in with that provider. The run saves the full
#                                    list in kilo-0-models.txt.
#
# Results land in spike/host-matrix/results/<time>/ (ignored by git, because the
# answers contain local paths).

set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/results/$(date +%Y%m%d-%H%M%S)"
PROJECT="$(mktemp -d)"
LIMIT=240   # seconds per prompt
mkdir -p "$OUT"

newest() { ls -d $1 2>/dev/null | sort -V | tail -1; }
CLAUDE="$(newest "$HOME/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude")"
CODEX="$(newest "$HOME/.vscode/extensions/openai.chatgpt-*/bin/macos-aarch64/codex")"
KILO="$(newest "$HOME/.vscode/extensions/kilocode.kilo-code-*/bin/kilo")"

# --- test skills: real copy in ~/.agents/skills, link from ~/.claude/skills,
# --- the same layout the `skills` installer already uses on this machine.
mkdir -p "$HOME/.agents/skills" "$HOME/.claude/skills"
for s in cg-spike-hello cg-spike-auto; do
  rm -rf "$HOME/.agents/skills/$s" "$HOME/.claude/skills/$s"
  cp -R "$HERE/skills/$s" "$HOME/.agents/skills/$s"
  ln -s "../../.agents/skills/$s" "$HOME/.claude/skills/$s"
done
cleanup() {
  for s in cg-spike-hello cg-spike-auto; do
    rm -rf "$HOME/.agents/skills/$s" "$HOME/.claude/skills/$s"
  done
  rm -rf "$PROJECT"
}
trap cleanup EXIT

# --- a throwaway project with one marker per instructions file
cd "$PROJECT" && git init -q
echo "Marker for the host test: CG-SPIKE-POINTER-AGENTS" > AGENTS.md
echo "Marker for the host test: CG-SPIKE-POINTER-CLAUDE" > CLAUDE.md

P1='Do not run any tool. Answer only from what is already in your context. (a) List every skill you can see whose name starts with cg-spike. If one appears more than once, list it once per appearance. (b) For each, say whether you may invoke it yourself or only the human may. (c) Which of these markers appear in your instructions: CG-SPIKE-POINTER-AGENTS, CG-SPIKE-POINTER-CLAUDE? (d) Name your todo tool and your subagent tool, or say none.'
P2='/cg-spike-hello'
P3='I saw a purple heron today.'
P4='Please run the host probe.'

run() {  # run <label> <command...>
  local label="$1"; shift
  echo ">> $label"
  { echo "\$ $*"; echo; perl -e 'alarm shift; exec @ARGV' "$LIMIT" "$@"; echo; echo "[exit code: $?]"; } \
    > "$OUT/$label.txt" 2>&1 < /dev/null
}

want() { [ -z "${ONLY:-}" ] || [ "$ONLY" = "$1" ]; }

if ! want claude; then :
elif [ -x "$CLAUDE" ]; then
  run claude-0-version "$CLAUDE" --version
  ALLOW=(--allowedTools "Skill" "Read" "Bash(python3:*)" "Bash(python:*)")
  run claude-1-inventory  "$CLAUDE" -p "$P1"
  run claude-2-invoke     "$CLAUDE" -p "$P2" "${ALLOW[@]}"
  run claude-3-auto       "$CLAUDE" -p "$P3" "${ALLOW[@]}"
  run claude-4-no-auto    "$CLAUDE" -p "$P4" "${ALLOW[@]}"
  # Same project, but CLAUDE.md only imports AGENTS.md: does the AGENTS marker load?
  echo "@AGENTS.md" > CLAUDE.md
  run claude-5-import     "$CLAUDE" -p "$P1"
  echo "Marker for the host test: CG-SPIKE-POINTER-CLAUDE" > CLAUDE.md
else echo "Claude Code binary not found" > "$OUT/claude-missing.txt"; fi

if ! want codex; then :
elif [ -x "$CODEX" ]; then
  run codex-0-version "$CODEX" --version
  run codex-0-help    "$CODEX" exec --help
  run codex-1-inventory "$CODEX" exec --skip-git-repo-check "$P1"
  run codex-2-invoke    "$CODEX" exec --skip-git-repo-check "\$cg-spike-hello"
  run codex-2b-invoke-slash "$CODEX" exec --skip-git-repo-check "$P2"
  run codex-3-auto      "$CODEX" exec --skip-git-repo-check "$P3"
  run codex-4-no-auto   "$CODEX" exec --skip-git-repo-check "$P4"
else echo "Codex binary not found" > "$OUT/codex-missing.txt"; fi

if ! want kilo; then :
elif [ -x "$KILO" ]; then
  KM=(); [ -n "${KILO_MODEL:-}" ] && KM=(-m "$KILO_MODEL")
  run kilo-0-version "$KILO" --version
  run kilo-0-help    "$KILO" run --help
  run kilo-0-models  "$KILO" models
  run kilo-1-inventory "$KILO" run ${KM[@]+"${KM[@]}"} "$P1"
  run kilo-2-invoke    "$KILO" run ${KM[@]+"${KM[@]}"} "$P2"
  run kilo-3-auto      "$KILO" run ${KM[@]+"${KM[@]}"} "$P3"
  run kilo-4-no-auto   "$KILO" run ${KM[@]+"${KM[@]}"} "$P4"
else echo "Kilo binary not found" > "$OUT/kilo-missing.txt"; fi

echo
echo "Done. Results are in:"
echo "  $OUT"
echo "Tell the build session the run finished; it will read them and fill in docs/adr/0001-host-matrix.md."
