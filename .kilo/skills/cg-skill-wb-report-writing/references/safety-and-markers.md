# Safety Guardrails and Marker Grammar

## Non-Negotiable Guardrails

- Institutional position guardrail: never present ungrounded claims as cleared
  Bank guidance.
- Unpublished data guardrail: preserve unpublished or preliminary status.
- Country-sensitive guardrail: require approved terminology and framing.
- Fabrication guardrail: never invent numeric facts, dates, or citations.

## Marker Grammar (exact forms)

Use these forms exactly:

- [VERIFY: claim or citation]
- [SOURCE NEEDED: fact or figure]
- [INSTITUTIONAL POSITION: confirm reflects cleared Bank guidance]
- [PRELIMINARY: subject to revision]
- [UNPUBLISHED: DO NOT CIRCULATE]
- <!-- AUTHOR NOTE: explain drafting decision or reviewer context -->

## Marker Semantics

- Visible bracket markers communicate verification state in output text.
- Hidden HTML comment markers are for author notes only.
- Never convert hidden author notes into visible claims.

## Carry-Forward Rules

- Summarization must survive marker semantics and unresolved items.
- Document conversion must carry forward all unresolved markers.
- Adaptation across document types must preserve verification status.

## Citation and Position Safety

- Use citation structure only for verifiable entries.
- If a citation cannot be verified, keep [VERIFY: ...] or [SOURCE NEEDED: ...].
- Never fabricate an institutional position to fill missing policy language.
