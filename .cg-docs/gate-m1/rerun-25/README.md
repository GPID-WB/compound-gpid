# Gate rerun 25

Run on `77851d88`, task 2.9 as built and before its review, for Codex and the two Kilo shapes, one after the other.
Claude Code was left out while the account was at its Fable 5.2 limit. This is the first rerun with step R: the
review of the work of step W, and the human's decision on each finding.

- Codex: 43 of 44. Step R held end to end. The review showed six findings (F1 to F6) with their priorities, asked
  for a decision on each, answered "Yes." with the question again, and recorded "all accept: ..." on every finding
  with nothing left waiting. The one check that failed: the verifier of P4 did not rerun the checks. Its kickoff
  did not say that it might read the survey data, so it kept the data closed, as `worker.md` says, and returned
  INCONCLUSIVE. The kickoff of a verifier that reruns checks does not carry the data rule the human gave.
- Kilo: 29 of 44. In step C, after the human's yes, the agent ran `tier` again on the same facts. The new record
  carried the stop again, the yes no longer covered it, and `evidence` refused to run the test. The quick work stayed
  waiting on the human. In step W the agent read that waiting report as the stop of the new work and asked for a yes
  to it in eight turns, so W and R never started.
- Kilo with the panel's shape: 25 of 44. In step B the agent asked also for the organization's ordered levels of
  classification, which setup does not need, and then for a second yes to its proposal; the script's turns ran out
  before setup was written, and steps C and W failed in turn. In step W it went into an amendment loop as in rerun 24.

Codex passing step R, and the two Kilo shapes failing in steps B and C that task 2.9 did not change, put most of the
Kilo failures on the agent run rather than on the text of task 2.9. Two points are for the review of task 2.9: the
data rule in the kickoff of the verifier of P4, and whether a second `tier` on the same facts and files should keep
the human's yes.

The transcripts were cleaned by the sanitizer of `d2eafc91`; none holds a name, an address or a home folder.
