### review stage

> Read ~/.agents/skills/cg/worker.md before anything else.

You are the verifier `simplicity`. You check one principle, P6 Smallest change, simplest design, at the review stage, and nothing else. Read these files in full, in this order: what every verifier does; your principle, whose section "Verifier" says what to inspect at this stage, what to flag, how to prove a flag and what to leave alone; and your lens, when a third file is listed. Write each finding down as rule 4 of the first file says.

1. ~/.agents/skills/cg/verifier.md
2. ~/.agents/skills/cg/principles/P06-smallest-change.md
3. ~/.agents/skills/cg/lenses/simplicity.md

The project root: <project>
Under review: every file that differs from commit 2e628859c2de3ad6f721a6d27259a6307805865d (`git diff 2e628859c2de3ad6f721a6d27259a6307805865d`), each file that no commit holds (`git status --short`), and the work report .cg-docs/work-reports/2026-11-27-poverty-brief.md
The contract: the plan .cg-docs/plans/2026-11-27-poverty-brief.md, which the human approved as the record .cg-docs/approvals/2026-11-27-poverty-brief.7e093512474ab9ac.1.json holds it
What code recorded: .cg-docs/evidence/2026-11-27-poverty-brief/ and .cg-docs/approvals/
A run that code records: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run "<the command>" --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Every check of the plan, rerun by code: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --rerun --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Only the verifier `verification` runs the line above, once. Any other verifier leaves it, and reads the record of that rerun, `"kind": "rerun"`, when there is one.

Return one verdict block, as `verifier.md` gives it, and nothing else.

principle: P6
verdict: FLAG
findings:
  - checks/headcount.py:5: This change only reformats the existing check and is not part of the plan. (P2; fix: put the line back as the commit holds it)
  - pipeline.py:19-21: `members()` has one caller and only filters rows for that caller. (P3; fix: write its body at its one caller)
  - pipeline.py:24: `by_region()` does not read its `scale` argument, and the plan does not require that option. (P2; fix: remove `scale` from the function and its calls)
  - pipeline.py:31-32: `share_text()` has no caller, and the project does not expose it as an entry point. (P2; fix: take out the function)
note: Set aside the one-caller flag for `by_region()` because its name tells the reader what it does. The scope record is `.cg-docs/evidence/2026-11-27-poverty-brief/0004-20261127T142141Z-scope.json`.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/worker.md
→ Read ~/.agents/skills/cg/verifier.md
→ Read ~/.agents/skills/cg/principles/P06-smallest-change.md
→ Read ~/.agents/skills/cg/lenses/simplicity.md

# Todos
[•] Inspect contract, evidence records, and review diff
[ ] Assess P6 findings and return verdict block

→ Read .cg-docs/work-reports/2026-11-27-poverty-brief.md
→ Read .cg-docs/plans/2026-11-27-poverty-brief.md
✱ Glob "**/*" in .cg-docs/evidence/2026-11-27-poverty-brief · 4 matches
✱ Glob "*.json" in .cg-docs/approvals · 2 matches

$ git diff --stat 2e628859c2de3ad6f721a6d27259a6307805865d && git diff --name-status 2e628859c2de3ad6f721a6d27259a6307805865d && git status --short
checks/headcount.py |  6 +++---
 pipeline.py         | 18 ++++++++++++++++++
 2 files changed, 21 insertions(+), 3 deletions(-)
M	checks/headcount.py
M	pipeline.py
 M checks/headcount.py
 M pipeline.py
?? .cg-docs/
?? checks/table.py
?? output/

→ Read pipeline.py
→ Read checks/table.py
→ Read checks/headcount.py
→ Read .cg-docs/approvals/2026-11-27-poverty-brief.e3efad148b4723ba.1.json
→ Read .cg-docs/approvals/2026-11-27-poverty-brief.7e093512474ab9ac.1.json
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0004-20261127T142141Z-scope.json

$ git diff --unified=80 2e628859c2de3ad6f721a6d27259a6307805865d -- pipeline.py checks/headcount.py
diff --git a/checks/headcount.py b/checks/headcount.py
index f8d2b35..e4c7de5 100644
--- a/checks/headcount.py
+++ b/checks/headcount.py
@@ -1,9 +1,9 @@
 """The check of the headcount ratio: python checks/headcount.py"""
 import csv
 import sys
 
-EXPECTED=52/110  # the worked example: 52 of the 110 units of weight lie below the line
+EXPECTED = 52 / 110  # the worked example: 52 of the 110 units of weight lie below the line
 
 with open("output/headcount.csv", newline="", encoding="utf-8") as handle:
-    found=float(next(csv.DictReader(handle))["headcount"])
-sys.exit(0 if abs(found-EXPECTED)<1e-6 else 1)
+    found = float(next(csv.DictReader(handle))["headcount"])
+sys.exit(0 if abs(found - EXPECTED) < 1e-6 else 1)
diff --git a/pipeline.py b/pipeline.py
index 84a3815..21e7daf 100644
--- a/pipeline.py
+++ b/pipeline.py
@@ -1,27 +1,45 @@
 """Make the outputs of the poverty brief from the survey: python pipeline.py"""
 import csv
 import os
 
 LINE = 3.0  # the poverty line, a day
 
 
 def households():
     with open("data/survey.csv", newline="", encoding="utf-8") as handle:
         return list(csv.DictReader(handle))
 
 
 def headcount(rows):
     """The weighted share of the households below the line."""
     total = sum(float(row["weight"]) for row in rows)
     return sum(float(row["weight"]) for row in rows if float(row["welfare"]) < LINE) / total
 
 
+def members(rows, region):
+    """The households of one region."""
+    return [row for row in rows if row["region"] == region]
+
+
+def by_region(rows, scale=1.0):
+    """The headcount ratio of each region."""
+    if LINE < 0:
+        raise ValueError("the poverty line is negative")
+    return {region: headcount(members(rows, region)) for region in sorted({row["region"] for row in rows})}
+
+
+def share_text(share):
+    return f"{100 * share:.1f}%"
+
+
 def main():
     rows = households()
     os.makedirs("output", exist_ok=True)
     with open("output/headcount.csv", "w", encoding="utf-8") as out:
         out.write(f"headcount\n{headcount(rows):.6f}\n")
+    with open("output/table.csv", "w", encoding="utf-8") as out:
+        out.write("region,headcount\n" + "".join(f"{name},{share:.6f}\n" for name, share in by_region(rows).items()))
 
 
 if __name__ == "__main__":
     main()

# Todos
[✓] Inspect contract, evidence records, and review diff
[✓] Assess P6 findings and return verdict block



[exit code: 0]

### plan stage

> Read ~/.agents/skills/cg/worker.md before anything else.

You are the verifier `simplicity`. You check one principle, P6 Smallest change, simplest design, at the plan stage, and nothing else. Read these files in full, in this order: what every verifier does; your principle, whose section "Verifier" says what to inspect at this stage, what to flag, how to prove a flag and what to leave alone; and your lens, when a third file is listed. Write each finding down as rule 4 of the first file says.

1. ~/.agents/skills/cg/verifier.md
2. ~/.agents/skills/cg/principles/P06-smallest-change.md
3. ~/.agents/skills/cg/lenses/simplicity.md

The project root: <project>
Under review: .cg-docs/plans/2026-11-26-poverty-brief.md
The contract: in the plan itself; the human decided the intent it is built on, .cg-docs/brainstorms/2026-11-27-poverty-brief.md
What code recorded: none
A run that code records: none at this stage, so point at a file and a line
Every check of the plan, rerun by code: none at this stage
Only the verifier `verification` runs the line above, once. Any other verifier leaves it, and reads the record of that rerun, `"kind": "rerun"`, when there is one.

Return one verdict block, as `verifier.md` gives it, and nothing else.

I will read the required verifier instructions and plan materials in the stated order, then report only the P6 verdict.
The P6 plan-stage lens directs review of the plan and existing code. I will now read the contract, plan, and project code needed to judge whether slices are required or can be smaller.
principle: P6
verdict: FLAG
findings:
  - .cg-docs/plans/2026-11-26-poverty-brief.md:54: S1 plans to deliver a regional table that `pipeline.py` already writes, so remove the slice unless it requires a change not shown in the plan (P2; fix: drop S1).
  - .cg-docs/plans/2026-11-26-poverty-brief.md:55: S2 adds a scaling option that no requirement asks for (P2; fix: drop S2).
  - .cg-docs/plans/2026-11-26-poverty-brief.md:56: S3 adds a negative-line check even though the contract fixes the line at 3.0 (P3; fix: drop S3).
  - .cg-docs/plans/2026-11-26-poverty-brief.md:57: S4 plans to lay out again a check that already exists in `checks/headcount.py` (P2; fix: keep the existing check and drop S4).
note: Inspected the plan, its human-decided intent, and existing project code. No code rerun applies at the plan stage. Left the contract requirements and human decision unchanged.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/worker.md
→ Read ~/.agents/skills/cg/verifier.md
→ Read ~/.agents/skills/cg/principles/P06-smallest-change.md
→ Read ~/.agents/skills/cg/lenses/simplicity.md
→ Read .cg-docs/plans/2026-11-26-poverty-brief.md
→ Read .cg-docs/brainstorms/2026-11-27-poverty-brief.md
✱ Glob "**/*" in . · 19 matches
→ Read pipeline.py
→ Read README.md
→ Read checks/headcount.py
→ Read checks/table.py


[exit code: 0]
