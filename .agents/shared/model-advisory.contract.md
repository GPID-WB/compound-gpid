# Model Advisory Contract

## Purpose

This contract provides capability and reasoning-effort advice without controlling
execution. The active platform picker or configuration, not Compound GPID, is
the source of truth for the model and effort used for a task.

The contract is advisory data. It must never be translated into prompt or agent frontmatter, a target mapping, a dispatch instruction, a retry rule, or a model switch.

## Stable Stages

The canonical stage identifiers are:

| Stage | Transition | Capability profile |
|-------|------------|--------------------|
| `planning` | `/cg-plan` to implementation | Repository navigation, decomposition, dependency awareness, and test planning. |
| `implementation` | `/cg-work` to review | Reliable code and configuration changes, tool use, test-driven iteration, and narrow diffs. |
| `review` | `/cg-review` to fix triage | Independent critical reasoning, evidence checking, risk classification, and adversarial comparison. |
| `fix-triage` | `/cg-fix-triage` to compounding/documentation | Finding-specific diagnosis, minimal safe fixes, regression awareness, and status tracking. |
| `compounding-documentation` | `/cg-compound` or documentation handoff | Faithful synthesis, provenance preservation, concise explanation, and safe knowledge capture. |

## Recommendation Shape

Each handoff recommendation contains:

- `stage`: one stable stage identifier above;
- `capabilityProfile`: the task capability needed, not a model identity;
- `effort`: one advisory label from `low`, `medium`, `high`, `xhigh`, or `max`;
- `rationale`: why the capability and effort fit the next task;
- `strongOption`: a capability-first option that prioritizes successful completion;
- `economicalOption`: an optional lower-cost option for bounded or straightforward work;
- `userControl`: an explicit statement that the user chooses the model and effort.

The strong option comes first. Token economy is considered only after effective
completion, correctness, and evidence needs are covered. A recommendation may
refer to a bundled example by an opaque `exampleRef`, but the reference is not
executable model metadata.

## Advisory Source Order

Resolve advice in this order and stop at the first valid source:

1. Reliable runtime or platform facts observed through a supported mechanism;
2. The user's optional local `model-advisory` configuration;
3. Bundled, dated examples in `model-advisory-examples.json` with explicit
   verification and availability status;
4. Capability-only guidance with no named example.

Missing, malformed, stale, or unsupported optional data must produce a visible
warning and fall through to the next source. It must never change execution.
Runtime catalog introspection is intentionally deferred until a supported
platform exposes a reliable mechanism.

## Local Override Shape

Users may add this optional block to `compound-gpid.local.md`:

```yaml
model-advisory:
  enabled: true
  examples:
    planning:
      strong: "example-id"
      economical: "example-id"
  preferences:
    effort: "high"
    notes: "Optional user context for advisory wording only."
```

Local values select advisory examples or describe preferences only. They do not
set a runtime model, change reasoning effort, alter platform configuration, or
dispatch another agent. Unknown example IDs, invalid effort labels, and
unsupported fields are warnings followed by source fallback.

## Cross-Family Review

When the generator family is known, the reviewer may recommend a different
family for independent contrast, subject to the user's availability and choice.
When the family is unknown or the platform reports Auto, say that a different
family could be useful if available; never infer the hidden identity or claim
that a cross-family review occurred.

## Prohibited Fields And Behaviors

Advisory artifacts and handoff prose must not contain executable routing fields
or behavior such as `model`, `preferredModel`, `modelMapping`, `setModel`,
`dispatchModel`, `switchModel`, `retryWithModel`, `exactModel`, or a platform
model assignment. Do not silently switch models, set effort, retry on another
model, guess an unknown vendor, or constrain the user's selection.

Every handoff must state that examples are suggestions, availability can differ by platform and date, and the user makes the final selection.
