### review stage

> Read ~/.agents/skills/cg/worker.md before anything else.

You are the verifier `simplicity`. You check one principle, P6 Smallest change, simplest design, at the review stage, and nothing else. Read these files in full, in this order: what every verifier does; your principle, whose section "Verifier" says what to inspect at this stage, what to flag, how to prove a flag and what to leave alone; and your lens, when a third file is listed. Write each finding down as rule 4 of the first file says.

1. ~/.agents/skills/cg/verifier.md
2. ~/.agents/skills/cg/principles/P06-smallest-change.md
3. ~/.agents/skills/cg/lenses/simplicity.md

The project root: <project>
Under review: every file that differs from commit c35331b7de1cbb20dfccb01d907f5a06b0348233 (`git diff c35331b7de1cbb20dfccb01d907f5a06b0348233`), each file that no commit holds (`git status --short`), and the work report .cg-docs/work-reports/2026-11-27-poverty-brief.md
The contract: the plan .cg-docs/plans/2026-11-27-poverty-brief.md, which the human approved as the record .cg-docs/approvals/2026-11-27-poverty-brief.d57a059aa4ef8100.1.json holds it
What code recorded: .cg-docs/evidence/2026-11-27-poverty-brief/ and .cg-docs/approvals/
A run that code records: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run "<the command>" --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Every check of the plan, rerun by code: "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --rerun --report ".cg-docs/work-reports/2026-11-27-poverty-brief.md" --project "<project>"
Only the verifier `verification` runs the line above, once. Any other verifier leaves it, and reads the record of that rerun, `"kind": "rerun"`, when there is one.

Return one verdict block, as `verifier.md` gives it, and nothing else.

principle: P6
verdict: FLAG
findings:
  - checks/headcount.py:4-6: The change only reformats the existing check, which the task does not require. (P2; fix: restore the file to its baseline layout)
  - pipeline.py:19-21: The one-caller helper extracts a simple filter that can be written at its call site. (P3; fix: put the filter body at its one caller)
  - pipeline.py:24: The function has an unused `scale` option that no requirement asks for. (P2; fix: remove `scale` from the function and its calls)
  - pipeline.py:31-32: No line in the project calls this function, and it is not an entry point. (P2; fix: remove the function)
note: The scope record also identifies `by_region` as a one-caller function; I set that finding aside because its name describes the regional-ratio operation at the call site. The rerun record was not present, and this verifier does not run it.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/worker.md
→ Read ~/.agents/skills/cg/verifier.md
→ Read ~/.agents/skills/cg/principles/P06-smallest-change.md
→ Read ~/.agents/skills/cg/lenses/simplicity.md

# Todos
[•] Inspect approved plan, scope evidence, and work report
[ ] Review changed files for P6 issues and prove candidate flags
[ ] Return the required verdict block

→ Read .cg-docs/plans/2026-11-27-poverty-brief.md
→ Read .cg-docs/work-reports/2026-11-27-poverty-brief.md
✱ Glob ".cg-docs/evidence/2026-11-27-poverty-brief/*" in . · 0 matches

$ git diff --name-status c35331b7de1cbb20dfccb01d907f5a06b0348233
M	checks/headcount.py
M	pipeline.py

$ git status --short
M checks/headcount.py
 M pipeline.py
?? .cg-docs/
?? checks/table.py
?? output/

→ Read .cg-docs/approvals/2026-11-27-poverty-brief.d57a059aa4ef8100.1.json
✱ Glob "**/*" in .cg-docs · 16 matches
✱ Glob "*.py" in . · 3 matches

$ git diff --unified=80 c35331b7de1cbb20dfccb01d907f5a06b0348233 -- pipeline.py checks/headcount.py
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

→ Read .cg-docs/verification.md
→ Read checks/table.py
→ Read .cg-docs/evidence/2026-11-27-poverty-brief/0009-20261127T123912Z-scope.json

$ git show c35331b7de1cbb20dfccb01d907f5a06b0348233:pipeline.py
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


def main():
    rows = households()
    os.makedirs("output", exist_ok=True)
    with open("output/headcount.csv", "w", encoding="utf-8") as out:
        out.write(f"headcount\n{headcount(rows):.6f}\n")


if __name__ == "__main__":
    main()

→ Read pipeline.py

# Todos
[✓] Inspect approved plan, scope evidence, and work report
[✓] Review changed files for P6 issues and prove candidate flags
[✓] Return the required verdict block



[exit code: 0]

### plan stage

> Read ~/.agents/skills/cg/worker.md before anything else.

You are the verifier `simplicity`. You check one principle, P6 Smallest change, simplest design, at the plan stage, and nothing else. Read these files in full, in this order: what every verifier does; your principle, whose section "Verifier" says what to inspect at this stage, what to flag, how to prove a flag and what to leave alone; and your lens, when a third file is listed. Write each finding down as rule 4 of the first file says.

1. ~/.agents/skills/cg/verifier.md
2. ~/.agents/skills/cg/principles/P06-smallest-change.md
3. ~/.agents/skills/cg/lenses/simplicity.md

The project root: <project>
Under review: .cg-docs/plans/2026-11-27-poverty-brief.md
The contract: in the plan itself; the human decided the intent it is built on, .cg-docs/brainstorms/2026-11-27-poverty-brief.md
What code recorded: none
A run that code records: none at this stage, so point at a file and a line
Every check of the plan, rerun by code: none at this stage
Only the verifier `verification` runs the line above, once. Any other verifier leaves it, and reads the record of that rerun, `"kind": "rerun"`, when there is one.

Return one verdict block, as `verifier.md` gives it, and nothing else.

principle: P6
verdict: FLAG
findings:
  - .cg-docs/plans/2026-11-27-poverty-brief.md:56: S2 adds a scale option that no requirement asks for. (P2; fix: remove S2 and the option from S1)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:57: S3 adds a negative-poverty-line check even though the plan fixes the line at 3.0 and no requirement asks for this check. (P3; fix: remove S3)
  - .cg-docs/plans/2026-11-27-poverty-brief.md:58: S4 lays out the whole-survey check again even though the existing `checks/headcount.py` already checks the unchanged ratio. (P2; fix: keep the existing check and remove S4)
note: The human chose to put the table in the same script, so that design is left unchanged. The `simplicity` lens says no code has run at the plan stage; no recorded scope result was used.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/worker.md
→ Read ~/.agents/skills/cg/verifier.md
→ Read ~/.agents/skills/cg/principles/P06-smallest-change.md
→ Read ~/.agents/skills/cg/lenses/simplicity.md

# Todos
[•] Inspect plan and relevant project code for P6 concerns
[ ] Return the required single verdict block

→ Read .cg-docs/plans/2026-11-27-poverty-brief.md
✱ Glob "**/*" in . · 23 matches
→ Read pipeline.py
→ Read checks/table.py
→ Read checks/headcount.py
→ Read .cg-docs/brainstorms/2026-11-27-poverty-brief.md

# Todos
[✓] Inspect plan and relevant project code for P6 concerns
[✓] Return the required single verdict block



[exit code: 0]
