# Capture a Solution

## When to Capture

Capture a solution when:
- You fixed a tricky bug that took more than a few minutes
- You discovered a useful pattern or technique
- You solved an environment or build issue
- You found a performance optimization
- You think "someone else on the team will hit this"

## Process

### 1. Identify the Problem
- What went wrong? What were the symptoms?
- What error messages appeared?
- What was the context (language, package, OS)?

### 2. Identify the Root Cause
- Why did it happen?
- What was the underlying issue (not just the surface symptom)?
- Was it a configuration issue, code issue, or understanding issue?

### 3. Document the Solution
- What fixed it?
- Include the exact code or configuration change
- Note any prerequisites or dependencies

### 4. Add Prevention Guidance
- How can this be avoided in the future?
- Are there patterns to follow?
- Are there anti-patterns to avoid?
- Should a coding standard or instruction file be updated?

### 5. Categorize and Tag
- Choose the most appropriate category (see SKILL.md)
- Add relevant tags for searchability
- Set severity based on impact (P0/P1/P2/P3)
- Note the language (R, Python, both)

### 6. Cross-Reference
- Search `.cg-docs/solutions/` for related existing solutions
- Add links between related solutions
- If the solution reveals a broader pattern, consider updating instructions

## File Location

```
.cg-docs/solutions/<category>/YYYY-MM-DD-brief-description.md
```

## Quality Checklist

- [ ] Problem is described with symptoms (someone can recognize they have the same issue)
- [ ] Root cause is explained (not just "do this to fix it")
- [ ] Solution includes runnable code or exact steps
- [ ] Prevention section is actionable
- [ ] Tags are specific and searchable
- [ ] Related solutions are linked
