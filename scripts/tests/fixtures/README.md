# Characterization fixture

<!-- Created 2026-09-03. -->

`cg_characterization_manifest.json` is a repository-wide generated-target
baseline, so a CR ML bundle update also changes its platform entries. Before
the CR ML redesign, these twelve generated paths already had hashes that did
not match the committed fixture at `HEAD`:

- `.claude/commands/cg-setup.md`
- `.claude/commands/setup-templates.md`
- `.claude/skills/cg-skill-setup/SKILL.md`
- `.agents/commands/cg-setup.md`
- `.agents/commands/setup-templates.md`
- `.agents/skills/cg-skill-setup/SKILL.md`
- `.opencode/commands/cg-setup.md`
- `.opencode/commands/setup-templates.md`
- `.opencode/skills/cg-skill-setup/SKILL.md`
- `.kilo/commands/cg-setup.md`
- `.kilo/commands/setup-templates.md`
- `.kilo/skills/cg-skill-setup/SKILL.md`

They are refreshed here because the characterization test requires one exact
manifest for all generated assets. This is baseline repair, not a CR ML
behavior change; the entries should be isolated in a future characterization
maintenance change if the repository adopts per-feature manifests.