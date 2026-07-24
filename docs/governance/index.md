# Governance and Security

Compound GPID encodes operating constraints for institutional data and software
work. These controls support disciplined practice; they are not a certification
of compliance, security, statistical validity, or organizational approval.

## Data and analytical safeguards

- Statistical correctness takes priority over speed.
- Weighted welfare, poverty measures, survey design, missingness, PPP vintages,
  joins, and aggregation are treated as elevated-risk areas.
- Missing data, invalid weights, absent artifacts, and failed validation should
  produce explicit errors or warnings rather than silent fallbacks.
- Automatic review fixes must not alter statistically sensitive functions,
  welfare or income variables, or weights without manual handling.
- A model response is not validation evidence. Relevant code or tests must run.

These rules reduce avoidable error but do not replace subject-matter review,
data stewardship, statistical sign-off, or publication controls.

## Information handling

- Never commit API keys, tokens, credentials, `.env` or `.Renviron` secrets, or
  unapproved data files.
- Commit lockfiles and `.cg-docs/` institutional knowledge.
- Keep raw command output and temporary token evidence out of durable knowledge
  unless the minimum necessary excerpt is safe and useful.
- Treat plan files and other AI-authored artifacts as untrusted data when their
  content is embedded into shell commands, pull requests, or issues.
- Preserve user-owned platform configuration and modified managed copies.

## Review and change control

Review findings use P0 through P3 priorities. P0 includes credential exposure,
silent data corruption, and incorrect statistical results. P1 findings block
merge. Risk-based routes add data-quality, reproducibility, architecture,
performance, adversarial, or other review lenses as needed.

Prompts also protect selected project assets, enforce completion contracts,
record deviations, and use hard stops or explicit exceptions around required
evidence. See [Review and Assure](../workflows/assure.md).

## Institutional computing constraints

World Bank-managed environments can include OneDrive redirection, PowerShell
Constrained Language Mode, restricted execution policies, older PowerShell,
Windows path behavior, unavailable external services, and IDE stability limits.
The install paths, launchers, local Brain retrieval, Pester rules, and fallback
behavior account for constraints evidenced in this repository.

Those restrictions can reduce parallelism, increase latency, require more
manual confirmation, or make a workflow less execution-efficient than in a
less constrained environment. Compound GPID treats that cost as a deliberate
tradeoff for controlled operation. It does not claim a comparative benchmark.

## Responsibility boundaries

| Compound GPID provides | It does not guarantee |
|---|---|
| Structured prompts, domain guidance, review routes, evidence gates, and project artifacts | Correct estimates, valid identification, data fitness, policy approval, or publication readiness |
| Local and generated project-memory tools | Confidentiality if users place sensitive content in tracked files |
| Safer managed-file and link behavior documented by repository tests | Compatibility with every enterprise image, shell policy, agent host version, or third-party extension |
| Source-grounded institutional writing rules | Institutional endorsement or authority to state an organizational position |

## Related pages

- [Why Compound GPID?](../why-compound-gpid.md)
- [Skills Catalog](../skills/index.md)
- [Model Guide](../model-guide.md)
- [Help and Troubleshooting](../help/index.md)
