# Understand Skill Availability

Availability is reliable only when manifest health is `fresh`.

- `active` means the capability is selected and the current manifest proves it.
- `inactive` means the skill is known but is not selected.
- `prospective` means discovery used current registry data because the committed
  manifest is missing or stale.
- `invalid` means a contract failed and no runtime claim is safe.

Supported suite and platform metadata is eligibility, not activation. For a
project skill, only its one-to-one `selectedProjectSkills` entry selects the
bundle. Use [find](../commands/find.md), [info](../commands/info.md), and
[remediation](remediation.md) to distinguish these cases.
