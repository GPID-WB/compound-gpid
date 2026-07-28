# Operation Workflows

This file defines operation-level routing for the World Bank report-writing
skill and the shared source hierarchy.

## Source Hierarchy

Apply this order strictly:
1. User-provided cleared content and project data.
2. Verifiable cited sources.
3. Approved exemplars for the requested document type.
4. Explicit placeholders and markers.

Never silently promote a lower tier into a verified fact or institutional
position.

## Per-Type Preflight

Validator-enforced checks in this phase:
- 2-3 approved exemplars are available.
- intended audience is explicitly identified.
- required terminology is available or marked unresolved.
- required disclaimers are present when required.
- source links are verifiable URLs or repo-relative files.

Manual or child-plan checks (not validator-enforced in this phase):
- document-type rhetorical expectations and section composition details.
- nuanced disclaimer phrasing choices beyond explicit required entries.

Before producing final prose for a document type, verify:
- 2-3 approved exemplars are available.
- intended audience is explicitly identified.
- required terminology is available or marked unresolved.
- required disclaimers are present when needed.
- source links are verifiable URLs or repo-relative files.

If any check fails, return a missing-input list and stop for that type only.

## Operation Routing

### Draft

- Start from the highest available source tier.
- Keep unsupported facts in visible placeholder markers.
- Do not add uncited specificity.

### Expand Sections

- Preserve all existing markers and source status.
- Expand only claims grounded in supplied content.

### Revise

- Improve clarity and structure without changing evidence status.
- Retain caveats and uncertainty markers.

### Summarize

- Preserve unresolved verification markers.
- Do not remove institutional-position checks.

### Adapt Across Types

- Reframe structure and tone for target audience.
- Carry over unresolved claims as unresolved markers.

### Quality Review

- Apply checklist and marker integrity checks before acceptance.
- Return actionable corrections for safety or style gaps.

### End-to-End Production

- Route through preflight, drafting, revision, and quality review.
- Stop if required artifacts for the requested type are missing.
