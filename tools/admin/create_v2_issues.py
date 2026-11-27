"""Create the Compound GPID 2.0 milestones, labels and issues.

Safe to rerun: existing labels, milestones and issues (matched by exact title)
are reused, never duplicated. Pass --dry-run to print what would be created.
"""
import json
import re
import subprocess
import sys
import time

REPO = "GPID-WB/compound-gpid"
PLAN = ".cg-docs/plans/2026-11-24-compound-gpid-v2.md (branch `v2`)"
DRY = "--dry-run" in sys.argv
FABLE = "Fable 5.2 (review by Opus 5.5)"
OPUS = "Opus 5.5 (review by Fable 5.2)"
HUMAN = "Needs the maintainer at the keyboard; either model can assist"

MILESTONES = {
    "M0": ("v2 M0 Foundations", "Tested host facts, frozen v1, sources, principles and pack contract."),
    "M1": ("v2 M1 Walking skeleton", "First end-to-end slice on all four hosts. Go / no-go before building more."),
    "M2": ("v2 M2 Loop, ownership, enforcement", "The product: the guided loop, the two hard stops, and the principle verifiers."),
    "M3": ("v2 M3 Packs", "Language, research and writing packs ported. Runs in parallel with M2."),
    "M4": ("v2 M4 Pilot", "Real use by economists and a developer. Sets the order of M5 and M6."),
    "M5": ("v2 M5 Output packs", "views, brain, roadmap. Order set by the pilot."),
    "M6": ("v2 M6 Extra packs", "issues sync, wiki, audit, release, maintainer. Order set by the pilot."),
    "M7": ("v2 M7 Launch", "Migration, docs, name decision, 2.0 release."),
}

# (id, title, model, plan section, goal, deliverables, done-when, depends-on, absorbs)
T = [
 ("0.1", "Host matrix spike", HUMAN, "6.5, 9",
  "Replace assumptions about the four hosts with tested facts before anything depends on them.",
  ["A two-skill test plugin (one user-invoked skill with a script, one model-invoked skill) and a test checklist.",
   "Runs on one Mac and one World Bank Windows machine, in Copilot (VS Code or Positron), Kilo, Claude Code and Codex.",
   "`docs/adr/0001-host-matrix.md` with one row per host and test, each marked tested, with date and host version."],
  ["Recorded per host: where user-level skills are discovered; whether marketplace install from a GitHub repo works; what happens when both routes are present (duplicates)",
   "Recorded per host: the exact command name a user types for a skill installed each way; whether `disable-model-invocation` is honored",
   "Recorded per host: how a skill locates its own `scripts/` folder; which interpreter command launches Python on Windows (Store alias, `py -3`, OneDrive paths with spaces); how many approval prompts one script call costs",
   "Recorded per host: whether `AGENTS.md` / `CLAUDE.md` / `copilot-instructions.md` is always loaded; todo tool; subagent tool; behavior after context compaction",
   "One run on the weakest model Copilot users commonly pick",
   "Kill criteria written down: which results would force a change to the install route or to the guide design"],
  [], []),
 ("0.2", "Freeze v1 and open the v2 branch", OPUS, "9, 10",
  "Keep v1 installable and frozen while v2 is built in a clean tree.",
  ["`v1` branch and a final v1 tag; maintenance-only notice in the v1 README.",
   "`v2` branch pushed, with the approved plan at `.cg-docs/plans/2026-11-24-compound-gpid-v2.md`.",
   "Branch protection and CI adjusted so v1 workflows do not run against `v2`."],
  ["`v1` and `v2` exist on the remote", "A v1 user can still install from the v1 tag by the existing instructions",
   "Nothing on `main` changes until the 2.0 release"],
  [], []),
 ("0.3", "Sort the open v1 roadmap issues", OPUS, "9",
  "Decide the fate of the 44 open `cg:roadmap` issues so they stop competing with the v2 plan.",
  ["A table: each open issue marked absorbed by a v2 task, deferred, or out of scope, with one line of reasoning.",
   "A comment on each issue linking the v2 task that absorbs it."],
  ["Every open `cg:roadmap` issue has a verdict", "No issue is closed without the maintainer's explicit go-ahead",
   "Out-of-scope verdicts are recorded as `.out-of-scope/` entries"],
  ["0.6"], ["#73", "#69", "#74", "#83", "#84", "#89", "#68", "#71", "#81", "#82", "#86", "#63"]),
 ("0.4", "Sources record and working adoption ledger", FABLE, "5",
  "Make it exact which parts of the three reference repos Compound GPID is based on, so credit is correct.",
  ["`docs/adr/0002-sources.md`: repo, pinned commit, license, local clone path for each source.",
   "`THIRD_PARTY_NOTICES` with the three MIT copyright notices.",
   "`docs/adoption-ledger.md`: plan section 5 as a working table with one row per source component, its verdict, our target file and status."],
  ["Pinned commits match the local clones", "Every row of plan section 5 is in the ledger",
   "The rule 'read the source file in full before adapting it' is stated at the top of the ledger"],
  ["0.2"], ["#86", "#63"]),
 ("0.5", "Draft the ten principle files", FABLE, "4.1, 4.2",
  "Write the constitution before any playbook exists, because the playbooks and verifiers are derived from it.",
  ["`skills/cg/principles/P01..P10-*.md`, each with five fixed parts: statement and why; in production; evidence it leaves; verifier; deterministic checks.",
   "`skills/cg/principles/README.md`: index with one line and a 'when it applies' trigger per principle.",
   "`metadata.derived-from` in each file's frontmatter."],
  ["All ten files follow the same five-part structure", "Each verifier states what to inspect, how to prove a flag, and its output format",
   "The maintainer has reviewed and accepted the ten principles"],
  ["0.4"], ["#74"]),
 ("0.6", "Pack contract, scope policy and budgets", FABLE, "6.1, 6.6",
  "Fix the small contract between the core and packs, and the rules that keep v2 from regrowing.",
  ["`docs/adr/0003-packs.md`: the `pack.json` keys, discovery, the rule that packs reach the core only through the `cg.py` command line.",
   "`SCOPE.md`: a change needs an observed failure and must not be composable from what exists.",
   "`.out-of-scope/` folder with the first records; plugin `GLOSSARY.md`; a one-paragraph threat model.",
   "Budgets written as numbers a CI job can check."],
  ["`pack.json` has six keys or fewer", "Budgets: core tooling <= 2,500 lines; each pack's tooling <= 1,500; tests <= 1.5x code",
   "A cap can only be raised with a decision record and an equal deletion"],
  ["0.1"], ["#50", "#48"]),

 ("1.1", "Hub layout, manifests, pack index, version sync", OPUS, "6.1, 6.5",
  "Lay out the v2 repository as a hub of packs.",
  ["`packs/` (or the layout chosen in ADR 0003) with `core/` first.", "`marketplace.json`, `.claude-plugin/` manifests, root `plugin.json`.",
   "`tools/sync_version.py` with a `--check` mode."],
  ["One version source; `--check` fails CI on drift", "The hub URL appears in exactly one place besides the manifests",
   "v1 packaging directories are absent from `v2`"],
  ["0.2", "0.6"], []),
 ("1.2", "cg.py skeleton: doctor, status, new, packs", OPUS, "6.4, 6.6",
  "Start the deterministic tooling with the commands the walking skeleton needs.",
  ["`cg.py doctor` (Python, git, gh, install, duplicates; writes the per-machine launcher file).",
   "`cg.py status` (phase, active artifact, pending human decisions, next step, playbook to read, version check).",
   "`cg.py new <type>` and `cg.py packs`.", "pytest suite."],
  ["Standard library only; one implementation for macOS and Windows", "`status` output is identical on repeat runs with unchanged files",
   "Writes are atomic and one file per record", "Tests pass on macOS and Windows runners"],
  ["1.1"], []),
 ("1.3", "core pack: router, setup and quick playbooks, pointer block", FABLE, "6.4",
  "Give the user the one front door, `/cg`.",
  ["`skills/cg/SKILL.md`: router only, 100 lines or fewer, no process content.", "`playbooks/setup.md` and `playbooks/quick.md`, each with an ownership statement and a `Reply:` contract.",
   "The pointer block text (ten lines or fewer) that setup writes into `AGENTS.md` / `CLAUDE.md` / `copilot-instructions.md`."],
  ["`/cg` with no arguments runs `status` and follows the playbook it names", "Setup explores, proposes, confirms, then writes; it proposes packs from the files it finds",
   "The quick lane has no hard stop unless `cg.py tier` reports elevated risk, and still records evidence"],
  ["1.2", "0.5"], ["#82", "#81", "#80"]),
 ("1.4", "install.py with packs, profiles and v1 removal", OPUS, "6.5",
  "One install command, nothing linked into projects.",
  ["`install.py --packs ...`, `--profile economist|developer|everything`, `--add`, `--remove`, `--update`, `--uninstall`.",
   "Detection and removal of v1 links and stale user-level copies.", "`docs/install-block.md`: the single canonical install text."],
  ["Refuses a double install and says which copy to remove", "Leaves user-owned files untouched", "Works without Node; standard library only",
   "Tested on macOS and Windows with a OneDrive path containing spaces"],
  ["1.1", "0.1"], []),
 ("1.5", "Port lang-r as the first real pack", OPUS, "6.1, 7",
  "Prove the pack contract with real content, ported close to as-is.",
  ["`lang-r` pack with the 8 v1 R skills and a `pack.json`."],
  ["`cg.py packs` lists it", "Installs with `install.py --packs core,lang-r`", "Passes the skill linter and pack validator"],
  ["1.1", "0.6"], ["#47"]),
 ("1.6", "CI: skill linter, pack validator, pytest, budget gate", OPUS, "6.6, 5.1",
  "Treat the skills as software from the first commit.",
  ["`tools/lint_skills.py`: portable frontmatter keys, name equals folder, ASCII frontmatter, required sections, line budgets, dead links, path allowlist.",
   "`tools/validate_pack.py`, `tools/check_budgets.py`.", "One GitHub Actions workflow for `v2`."],
  ["A skill with a non-portable frontmatter key fails CI", "Exceeding a budget fails CI, not warns"],
  ["1.1"], ["#50", "#48"]),
 ("1.7", "M1 gate: one small task on a toy R project in all four hosts", HUMAN, "11",
  "Go / no-go before building the rest. From here on, every task is built with `/cg`.",
  ["A toy R project.", "Evidence of the run in each host, committed under `.cg-docs/`."],
  ["Install of `core` and `lang-r` by the documented route in under five minutes per host", "`/cg` runs setup and a quick task that ends with recorded evidence",
   "`cg.py status` reports the same state in every host", "No skill is listed twice", "Written go / no-go decision"],
  ["1.2", "1.3", "1.4", "1.5", "1.6"], []),

 ("2.1", "Artifact schema, v1 reader, validate, approve, tier", OPUS, "6.6",
  "Fix the files that carry work between phases and sessions.",
  ["Flat-frontmatter schema for intent, plan, work report, review, solution, decision.", "A reader for v1 `.cg-docs/` artifacts.",
   "`cg.py validate` (with `--strict` for project CI), `cg.py approve`, `cg.py tier`."],
  ["An existing v1 `.cg-docs/` folder is read without conversion", "`approve` stores the user's verbatim reply, git identity, time and plan hash",
   "`tier` is computed from declared facts (estimation, weights, published outputs, schemas, deletions), not from model opinion"],
  ["1.7"], ["#76", "#75", "#66"]),
 ("2.2", "Grilling primitive, restate, assumptions, brainstorm playbook", FABLE, "5.1, 5.2",
  "One interview primitive used everywhere a decision is needed.",
  ["`playbooks/brainstorm.md` and the grilling section it uses.", "Restate step: goal, out of scope, what a wrong result looks like.", "Assumptions block."],
  ["Facts are looked up by the agent; decisions are put to the user with a recommended answer", "The session ends only when nothing is silently assumed and the user confirms",
   "A list of replies that do not count as a yes"],
  ["2.1"], ["#73", "#70", "#56"]),
 ("2.3", "Plan playbook, hard stop 1, plan-stage verifiers", FABLE, "4.3",
  "The plan is the contract the human approves.",
  ["`playbooks/plan.md`: thin vertical slices, declared checks, boundaries, deferred scope.", "Dispatch of the plan-stage verifiers and their results shown with the plan."],
  ["Every check in the plan can fail", "The turn ends at approval; approval is written to the artifact", "An unfinished plan is never overwritten"],
  ["2.2", "2.5"], ["#83", "#84", "#88", "#89", "#67"]),
 ("2.4", "Work playbook: evidence, guard, stop rules, worker.md", FABLE, "4.3, 6.6",
  "Build in slices, with evidence recorded by code.",
  ["`playbooks/work.md`, `worker.md`.", "`cg.py evidence <check-id>`, `cg.py guard`."],
  ["`evidence` runs only checks declared in the approved plan; anything else is labelled ad hoc", "`guard` fails when the diff deletes or skips tests or adds suppressions",
   "Evidence stores a bounded digest, never data", "Irreversible actions always stop"],
  ["2.3"], ["#68", "#61", "#98"]),
 ("2.5", "Verifier engine: verifiers, conformance, kickoff texts", OPUS, "4.2",
  "Dispatch of principle verifiers is computed, not remembered.",
  ["`cg.py verifiers --stage <stage>` prints the verifiers to run and the kickoff text for each.", "`cg.py conformance` records a verdict per principle and blocks sign-off until all applicable ones are present.",
   "Pack lenses are merged into the dispatch list."],
  ["Kickoff text never includes the author's explanation", "A flag without proof is recorded as unverified",
   "The record states independent review or self-review"],
  ["2.1", "0.5"], []),
 ("2.6", "Determinism verifier and cg.py repro", FABLE, "4.3",
  "Enforce P3: anything code can produce or check is produced or checked by code.",
  ["The P3 verifier lens for plan time and review time.", "`cg.py repro`: run the declared pipeline twice and compare output digests."],
  ["Flags: outputs not regenerated by a script, numbers typed into prose, manual steps, unseeded randomness, unpinned environments, user-specific paths, order dependence",
   "Each flag proposes the code that would replace it", "Catches its planted violations"],
  ["2.5"], []),
 ("2.7", "Verification verifier", FABLE, "4.3",
  "Enforce P4: prove it works on the real artifact.",
  ["The P4 verifier lens."],
  ["Reruns every declared check itself", "Flags claims with no evidence, proxy evidence, checks that cannot fail, and statistics with no independent check",
   "Asks of every reported number what else it could be measuring", "Catches its planted violations"],
  ["2.5"], ["#68"]),
 ("2.8", "Adversary, Simplicity, Spec and Claims verifiers", FABLE, "4.3",
  "Enforce P5, P6, P1 and P7.",
  ["Four verifier lenses."],
  ["Adversary: findings reproduced, bounded to three rounds, dropped findings listed", "Each catches its planted violations"],
  ["2.5"], ["#64"]),
 ("2.9", "Review playbook with general lenses and human triage", FABLE, "5.1, 7",
  "One review step that replaces `/cg-review`, `/cg-fix-triage` and `/cg-verify-pr`.",
  ["`playbooks/review.md`.", "General lenses ported from the 17 v1 review agents.", "`cg.py route`."],
  ["Findings keep P0 to P3", "Standards findings and spec findings are reported separately", "The human triages; zero findings is a valid result"],
  ["2.6", "2.7", "2.8"], []),
 ("2.10", "Sign-off: Ownership and Record verifiers, defend-it brief, hard stop 2", FABLE, "4.3, 6.4",
  "The human signs that they can explain the work.",
  ["P2 and P8 verifier lenses.", "Defend-it brief template.", "Predict-then-check step for analysis work."],
  ["Sign-off is offered only when every applicable principle has a verdict", "Each flag is fixed or accepted with a written reason", "The conformance record is rendered for the human"],
  ["2.9"], ["#74", "#85"]),
 ("2.11", "Compound playbook and Lesson verifier", FABLE, "4.3",
  "Verified lessons become checks first, prose second.",
  ["`playbooks/compound.md`, P9 verifier lens, solution template."],
  ["A lesson is captured only if verified, durable and behavior-changing", "Where a check is possible, the check is written and shown to fail on the past mistake"],
  ["2.10"], ["#72"]),
 ("2.12", "Bugfix playbook", FABLE, "5.1, 5.2, 5.3",
  "Replace `/cg-fixbug`, `/cg-diagnose` and `/cg-fix-problems`.",
  ["`playbooks/bugfix.md`."],
  ["No hypothesis testing before a command that can go red exists", "Ranked hypotheses are shown to the user", "Regression check lands before the fix"],
  ["2.4"], ["#71"]),
 ("2.13", "Glossary and decision records", FABLE, "5.2",
  "Shared language and recorded reasoning.",
  ["`GLOSSARY.md` rules; `cg.py decide`; `.cg-docs/decisions/` and `.cg-docs/out-of-scope/`."],
  ["A decision record is offered only when hard to reverse, surprising, and a real trade-off", "The agent challenges terms that conflict with the glossary or the code"],
  ["2.1"], ["#69"]),
 ("2.14", "Status, help and understand playbooks", FABLE, "5.2, 5.3",
  "Catch-up, help that routes without starting work, and explanation on request.",
  ["`playbooks/status.md`, `playbooks/understand.md`, help section."],
  ["Status lists every decision waiting on the human, with evidence and a recommendation", "Help returns at most three candidates and never starts work"],
  ["2.1"], ["#82", "#81"]),
 ("2.15", "Planted-violation tests, routing evals, pressure cases; M2 gate", OPUS, "4.3, 11",
  "Prove the verifiers and gates work.",
  ["Fixtures: unweighted poverty headcount, hand-typed results table, unseeded bootstrap.", "Routing evals including descriptions of commonly co-installed skills.", "Pressure cases for both hard stops."],
  ["Each verifier flags its planted violation with proof, in two hosts", "Pressure cases do not get past a gate", "M2 gate result written down"],
  ["2.6", "2.7", "2.8", "2.10"], ["#77"]),

 ("3.1", "lang-stata and lang-python packs", OPUS, "6.1, 7", "Port the Stata and Python skills close to as-is.",
  ["Two packs with `pack.json`."], ["Pass linter and validator", "Install on their own"], ["1.5"], ["#49"]),
 ("3.2", "research pack with /cr, track and lenses", FABLE, "6.3, 7", "Give researchers their own door into the same engine.",
  ["`/cr` alias (about ten lines).", "Research track playbook overlay.", "15 research skills and 11 research lenses ported."],
  ["`/cr` enters the guide with the research track declared", "`/cg` names the pack and its install command when it detects research without it",
   "Silent correctness failures remain P0"], ["2.5", "1.5"], []),
 ("3.3", "writing-wb pack", OPUS, "6.1, 7", "Port World Bank report writing and document rendering.",
  ["Pack with `pack.json`."], ["Pass linter and validator"], ["1.5"], []),
 ("3.4", "Move research_evidence to its own repository", HUMAN, "6.2, 8", "Separate the application from the skills.",
  ["A `research-evidence` repository in `GPID-WB` with history preserved.", "The research pack points to it."],
  ["Its tests pass in the new repository", "The hub no longer carries it on `v2`"], ["3.2"], []),

 ("4.1", "Pilot with economists and a developer", HUMAN, "9, 11", "Let real use decide what comes next.",
  ["Two or three economists and one developer use v2 on real work, including someone who is not a developer."],
  ["Friction list filed as `dogfood` issues", "Observation of gate behavior: bare approvals or real engagement", "Ranking of the remaining packs", "Decision on whether to cut a gate"],
  ["2.15", "3.1", "3.2"], []),

 ("5.1", "views pack: HTML artifact views and dashboard", OPUS, "6.6", "Deterministic HTML as the human's review surface.",
  ["Markdown subset to self-contained HTML, one template, no CDN.", "Project dashboard page."],
  ["Byte-identical output on repeat runs on macOS and Windows", "A render failure warns and never blocks"], ["4.1"], []),
 ("5.2", "brain pack and core index, search, stale detection", OPUS, "6.6", "Find past solutions without loading them all.",
  ["`cg.py index`, `cg.py search` in core; topic-level brain in the pack."], ["Search returns pointers, not bodies", "Stale entries flagged from git"], ["4.1"], []),
 ("5.3", "roadmap pack", OPUS, "6.6", "Roadmap edits by code, not by a model.",
  ["`roadmap.json` operations: add, link, start, done, view.", "Tracker abstraction as verbs."], ["Deterministic output", "No model edits the JSON"], ["4.1"], ["#87", "#79"]),

 ("6.1", "issues sync pack", OPUS, "5.2", "GitHub issues tied to roadmap items.", ["Pack reusing the v1 issues logic, cut to fit the budget."], ["Within the pack budget"], ["5.3"], []),
 ("6.2", "wiki pack", OPUS, "7", "Project wiki.", ["Pack with its scripts."], ["Within the pack budget"], ["4.1"], []),
 ("6.3", "audit pack", OPUS, "7", "Token and context audit.", ["Pack with its scripts."], ["Within the pack budget", "Runs on the plugin's own skills"], ["4.1"], ["#51", "#65"]),
 ("6.4", "release pack and ship playbook", OPUS, "5.2, 5.3", "Commit, pull request and release notes.", ["`playbooks/ship.md` with a PR body contract.", "Release notes generated from `.cg-docs/`."], ["Within the pack budget"], ["4.1"], []),
 ("6.5", "maintainer pack", FABLE, "5.2", "Help other teams write good packs.", ["Skill authoring rules, linter and pack validator packaged for pack authors.", "A reusable CI workflow for outside pack repositories."], ["An outside repository can validate a pack with one workflow file"], ["1.6"], []),

 ("7.1", "Migration guide and legacy detection", OPUS, "6.5, 9", "Move v1 users in four documented steps.",
  ["Guide: v1 unlink and uninstall, `install.py`, `/cg` converts `compound-gpid.local.md` and splits `compound-gpid.context.md`."], ["Tested on a real v1 project", "No user-owned file is removed"], ["4.1"], ["#78"]),
 ("7.2", "Docs site with generated reference and acknowledgements", OPUS, "5.4", "A one-page start and honest credit.",
  ["One-page start, philosophy (kept), how it works, reference generated from the skills, acknowledgements generated by `tools/credits.py`."],
  ["A pilot user completes a task after reading only the start page", "Every derived file appears on the acknowledgements page"], ["4.1"], ["#86"]),
 ("7.3", "Name and organization decision", HUMAN, "8", "Decide the Bank-wide name and where the repositories live before many people install.",
  ["Collision check on the candidate names.", "Decision on a new organization and, if yes, the transfer."], ["Decided before the 2.0 announcement", "The hub URL changes in one place"], [], []),
 ("7.5", "Documentation matches v2 everywhere", OPUS, "9, amendments",
  "v2 changes what people type and see almost completely. Every page a person might read must describe v2, and stay that way.",
  ["An inventory of every documentation surface: README, CONTRIBUTING, AGENTS.md, the docs site (about 93 pages), in-skill help text, issue and pull request templates, release notes. Each marked rewrite, keep or retire.",
   "A page for v1 users that maps each old command to what they type now.",
   "`tools/check_docs.py`, a drift check: no page outside the migration guide names a retired command or file; every command, pack, principle and path a page names exists; the generated reference matches the skills.",
   "The drift check wired into CI. It is built with task 1.6 so it runs from the first v2 commit, and this task finishes the audit before release.",
   "Documentation text passes the glossary check (`tools/check_glossary.py`)."],
  ["Zero mentions of `/cg-*` or `/cr-*` v1 commands outside the migration guide", "Every page in the inventory has a verdict and the rewrites are done",
   "The drift check and the glossary check pass in CI on the docs", "A pilot user completes a first task using only the documentation",
   "From M1 on, any task that changes what a human types or sees updates the documentation in the same change"],
  ["7.1", "7.2"], ["#82", "#81"]),
 ("7.4", "Release 2.0", HUMAN, "9", "Ship.", ["Merge `v2` into `main`, announcement, v1 end date."], ["All gates in plan section 11 passed", "Budgets hold at release"], ["7.1", "7.2", "7.3"], []),
]


def gh(*args, input_text=None):
    r = subprocess.run(["gh", *args], capture_output=True, text=True, input=input_text)
    if r.returncode != 0:
        raise SystemExit(f"gh {' '.join(args[:4])} failed: {r.stderr.strip()}")
    return r.stdout


def body(t, numbers):
    tid, title, model, sec, goal, deliv, done, deps, absorbs = t
    out = [f"**Goal.** {goal}", "", "**Deliverables**"]
    out += [f"- {d}" for d in deliv]
    out += ["", "**Done when**"] + [f"- [ ] {d}" for d in done]
    if deps:
        out += ["", "**Depends on:** " + ", ".join(f"{d} (#{numbers[d]})" if d in numbers else d for d in deps)]
    if absorbs:
        out += ["", "**Absorbs or relates to v1 issues:** " + ", ".join(absorbs)]
    out += ["", f"**Suggested model:** {model}", f"**Plan:** section {sec} of {PLAN}",
            "", "From M1.7 onward this task is built with `/cg`; friction goes to a `dogfood` issue."]
    return "\n".join(out)


def keep_blocks(body):
    """The ClickUp link blocks in a body, which a rewrite of the tracking issue keeps."""
    return [m.group(0) for m in re.finditer(r"<!-- clickup-skills:(\S+) -->.*?<!-- /clickup-skills:\1 -->", body or "", re.S)]


def main():
    labels = {l["name"] for l in json.loads(gh("label", "list", "-R", REPO, "--limit", "200", "--json", "name"))}
    for name, color, desc in [("v2", "5319e7", "Compound GPID 2.0"), ("dogfood", "fbca04", "Friction found while building v2 with /cg")]:
        if name not in labels and not DRY:
            gh("label", "create", name, "-R", REPO, "--color", color, "--description", desc)
    ms = {m["title"]: m["number"] for m in json.loads(gh("api", f"repos/{REPO}/milestones", "-X", "GET", "-f", "state=all", "-f", "per_page=100"))}
    for key, (title, desc) in MILESTONES.items():
        if title not in ms and not DRY:
            ms[title] = json.loads(gh("api", f"repos/{REPO}/milestones", "-f", f"title={title}", "-f", f"description={desc}"))["number"]
    existing = {i["title"]: i["number"] for i in json.loads(gh("issue", "list", "-R", REPO, "--state", "all", "--limit", "500", "--label", "v2", "--json", "number,title"))} if "v2" in labels or not DRY else {}
    numbers = {}
    for t in T:
        tid, title = t[0], t[1]
        full = f"v2 {tid}: {title}"
        if full in existing:
            numbers[tid] = existing[full]
            continue
        if DRY:
            print("would create:", full)
            continue
        mtitle = MILESTONES["M" + tid.split(".")[0]][0]
        url = gh("issue", "create", "-R", REPO, "--title", full, "--label", "v2", "--milestone", mtitle, "--body-file", "-", input_text=body(t, numbers)).strip()
        numbers[tid] = int(url.rsplit("/", 1)[1])
        print(tid, url)
        time.sleep(1.5)
    if DRY:
        print(f"{len(T)} tasks, {len(MILESTONES)} milestones")
        return
    track_title = "Compound GPID 2.0: tracking issue"
    lines = ["Tracking issue for the v2 rebuild: principles that are enforced, one guide (`/cg`), a hub of packs.",
             "", f"Plan: {PLAN}", ""]
    for key, (mtitle, desc) in MILESTONES.items():
        lines += [f"### {mtitle}", desc, ""]
        lines += [f"- [ ] #{numbers[t[0]]} {t[0]} {t[1]}" for t in T if t[0].split(".")[0] == key[1:]]
        lines.append("")
    lines += ["**Standing rule:** from M1 on, any task that changes what a human types or sees updates the documentation in the same change, and the docs drift check (task 7.5) must pass.", ""]
    lines += ["Based on ideas from addyosmani/agent-skills, mattpocock/skills and cursor/plugins (pstack), all MIT licensed; see the adoption ledger in task 0.4."]
    if track_title in existing:
        old = json.loads(gh("issue", "view", str(existing[track_title]), "-R", REPO, "--json", "body"))["body"]
        lines += ["", *keep_blocks(old)]
        gh("issue", "edit", str(existing[track_title]), "-R", REPO, "--body-file", "-", input_text="\n".join(lines))
        print("tracking", existing[track_title], "updated")
    else:
        print("tracking", gh("issue", "create", "-R", REPO, "--title", track_title, "--label", "v2", "--body-file", "-", input_text="\n".join(lines)).strip())


if __name__ == "__main__":
    main()
