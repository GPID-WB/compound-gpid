---
date: 2026-04-17
title: "Template {{placeholder}} tokens inside HTML comments are substituted by .Replace() loop, corrupting generated output"
category: "bugs"
language: "both"
tags: [powershell, template, placeholder, replace, html-comment, copilot-instructions, generation, context-layer]
root-cause: "String.Replace() operates on the entire template string including HTML comments — any {{token}} syntax inside a comment is substituted with real config values, corrupting the comment text in every generated file"
severity: "P1"
---

# Template `{{placeholder}}` Tokens in HTML Comments Substituted by `.Replace()` Loop

## Problem

When adding a documentation comment to `copilot-instructions.template.md`, the
comment was written with `{{placeholder}}` tokens to describe the variables:

```html
<!-- TEMPLATE FILE — managed by New-CopilotInstructions in scripts/helpers.ps1.
     Placeholders: {{project-name}}, {{project-type}}, {{languages}}, {{review-depth}}.
     Do not edit .github/copilot-instructions.md directly. -->
```

Every generated `copilot-instructions.md` in consumer projects then contained:

```html
<!-- TEMPLATE FILE — managed by New-CopilotInstructions in scripts/helpers.ps1.
     Placeholders: My Poverty Project, analytical, R, standard.
     Do not edit .github/copilot-instructions.md directly. -->
```

The placeholder variable names disappeared and were replaced with the real config
values from the user's project. The bug was discovered during a verification review
— test runs still passed because no test checked the comment text, but every
consumer project would receive a corrupted, misleading HTML comment.

## Root Cause

`New-CopilotInstructions` applies substitution using PowerShell's `String.Replace()`
method on the **entire template string** — not selectively on content blocks:

```powershell
$output = $template.Replace('{{project-name}}', $projectName)
$output = $output.Replace('{{project-type}}', $projectType)
$output = $output.Replace('{{languages}}', $languages)
$output = $output.Replace('{{review-depth}}', $reviewDepth)
```

HTML comments are part of the string. There is no concept of "template content only"
vs "metadata comments only" in a flat string substitution pass. Any `{{token}}` that
matches a substitution key is replaced unconditionally, regardless of where in the
file it appears.

The regex operator `-replace` would have the same problem.

## Solution

Remove `{{token}}` syntax from all HTML comments in the template. Use plain text
descriptions that do not use the `{{}}` delimiter:

```html
<!-- compound-gpid:template — source for copilot-instructions.md, managed by scripts/helpers.ps1.
     Run `cg-update` to regenerate the output file from this template.
     Do not edit .github/copilot-instructions.md directly.
     Template variables substituted at generation time: project-name, project-type, languages, review-depth. -->
```

The comment accurately documents the variables without using tokens that the
substitution engine recognises.

## Prevention

**Rule: never use `{{token}}` syntax anywhere in a template file except at the
exact substitution sites.** This includes:
- HTML comments (`<!-- ... -->`)
- Markdown comments (`[//]: # (...)`)
- YAML frontmatter comments (`# ...`)
- Any inline documentation that happens to reference the token names

If you need to document the list of tokens within the template itself, write the
variable names as plain text or use an alternative delimiter (e.g. `<project-name>`,
`$project-name`, or a prose description like "the project-name value").

**Review checklist for template files**: before committing a change to any `.template.md`
file, grep for `{{` and verify that every match is a real substitution site — not
documentation, examples, or comments.

## Related

- [ps51-utf8-bom-em-dash-corrupts-ast-silently.md](../bugs/2026-03-23-ps51-utf8-bom-em-dash-corrupts-ast-silently.md) — another silent template/file generation corruption in PS5.1
- `scripts/helpers.ps1` — `New-CopilotInstructions` function
- `.github/copilot-instructions.template.md` — the template file where the fix was applied
