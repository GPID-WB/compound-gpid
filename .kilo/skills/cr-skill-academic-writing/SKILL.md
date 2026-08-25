---
name: cr-skill-academic-writing
module: research
description: "Academic writing conventions for economics research papers.
  Covers journal style (AER, JPE, QJE, Econometrica), section structure,
  abstract writing, equation exposition, notation introduction discipline,
  citation style, and response-to-referee patterns. Loaded by
  @cr-academic-writing for Writing tasks."
---

# Academic Writing for Economics Research

Reference skill for writing and reviewing academic economics papers. Load for
all Writing task types.

---

## 1. Journal Style Conventions

### Top-5 Econ Journals — Common Denominators

All top economics journals (AER, JPE, QJE, REStud, Econometrica) share these
baseline expectations:

- **No bold** for emphasis — use italics sparingly or restructure the sentence
- **Author-year citations** — `(Smith, 2001)` not footnotes for academic references
- **Third person** throughout — not "we show" in abstract, "I show" only in
  sole-authored work
- **Active voice** preferred — "We estimate" not "It is estimated"
- **Footnotes** for caveats, not for important arguments
- **No bullet lists** in body text — prose paragraphs only
- **Oxford comma** — "X, Y, and Z"

### Journal-Specific Differences

| Journal | Word limit | Key style notes |
|---------|-----------|-----------------|
| **AER** | 10,000 (articles) | Author-year in text; numbered equations only if referenced |
| **JPE** | No hard limit | Prefers terse exposition; fewer robustness tables |
| **QJE** | No hard limit | Longer introductions standard; more reduced-form evidence |
| **Econometrica** | No hard limit | Theorem-proof format for theory; strict notation discipline |
| **REStud** | 10,000 | Similar to AER; less tolerance for long introductions |

When journal is unknown or not specified, default to AER conventions.

---

## 2. Section Structure

### Introduction (the most important section)

Follow the four-paragraph structure common in top economics journals:

1. **Hook** — motivating fact, statistic, or policy question (1–2 sentences)
2. **Gap** — what existing literature does not address or gets wrong
3. **Contribution** — what this paper does and what it finds (be specific)
4. **Preview** — roadmap of sections

The introduction must state the main finding clearly and quantitatively. "We find
that X increases Y by Z%" is better than "We find evidence of a positive
relationship between X and Y."

**Literature review placement**: Brief in-text citations in the introduction;
a dedicated related-literature section comes after the introduction or after
the model section (journal-dependent). Never end the introduction with a roadmap
paragraph alone — the main result must appear before the roadmap.

### Model / Methodology Section

- State assumptions before deriving results
- Every assumption should have economic motivation (one sentence minimum)
- Define all notation on first use
- End with the estimating equations (what goes into the data)

### Data Section

- Describe the population, sample construction, and restrictions in order
- Table of summary statistics should come here or immediately after
- Variable names in the text must match variable names in tables

### Results Section

- Lead with the main finding, then the table/figure
- Interpret magnitudes — "a one standard deviation increase in X…"
- Report coefficient and standard error; interpret as effect size, not just significance

### Robustness Section

- Vary one dimension at a time
- Explicitly state what threat to validity each robustness check addresses
- Do not report dozens of robustness tables without explanation

### Conclusion

- Summarize findings (2–3 sentences)
- State policy implications or broader significance
- Identify limitations and future research directions
- Do **not** introduce new results or new evidence

---

## 3. Abstract Writing

### Target Format

150 words (hard cap for most journals). Four-sentence structure:

1. **Motivation** — the research question and why it matters
2. **Method** — what variation you use and what data
3. **Finding** — the main quantitative result
4. **Implication** — why anyone should care

### Example Skeleton

> "We study how [X] affects [Y], motivated by [policy context or gap].
> Using [identification strategy] from [data], we estimate [method].
> We find that [main quantitative result].
> Our results suggest [policy/theoretical implication]."

### Anti-Patterns

- "We study the relationship between X and Y" — too vague; state the direction
- "We find that X is significant" — report the magnitude, not the p-value
- "Our paper contributes to the literature on..." — belongs in intro, not abstract
- Methodological jargon without plain-language translation

---

## 4. Equation Exposition

### Before Presenting

Introduce every equation in prose before displaying it:
> "The individual's problem is to maximize utility subject to the budget
> constraint:"

Not just dropping the equation with no lead-in.

### After Presenting

Follow every non-obvious equation with an interpretation sentence:
> "where $\beta$ captures the elasticity of substitution between capital and labor."

### Equation Numbering

Number only equations that are referenced elsewhere in the text. Use `\label{}`
and `\eqref{}` in LaTeX. Numbering every equation clutters the paper.

### Notation Best Practices

- Keep subscripts minimal — `i` for individual, `t` for time, `j` for product;
  avoid multi-letter subscripts except for standard abbreviations (`it`, `ijt`)
- Avoid re-using the same letter for different objects in the same paper
- Don't decorate: $\hat{\beta}_{OLS,IV,robust}$ — choose one decoration at a time
- Use standard notation: $\beta$ for coefficients, $\varepsilon$ for errors,
  $\mathbb{E}$ for expectation, $\mathbf{1}\{\cdot\}$ for indicator

---

## 5. Notation Introduction Discipline

### Define on First Use

Every symbol must be defined the first time it appears, in the sentence where it
appears:
> "Let $w_{it}$ denote the log wage of worker $i$ in period $t$."

Never: "where all variables are defined above" — specify what $w_{it}$ is.

### Notation Table

For papers with more than ~15 symbols, include a notation table as an appendix
or at the beginning of the model section. Format:

| Symbol | Definition |
|--------|-----------|
| $Y_{it}$ | Log household consumption per capita |
| $D_{it}$ | Treatment indicator: 1 if household received transfer |

### Consistency Across Sections

- Use the same symbol in the model and the empirical specification
- If the data uses a different variable name (`pcexp`), note the mapping:
  "In the notation of Section 2, $Y_{it}$ corresponds to `log_pcexp` in
  our data."

---

## 6. Citation Style

### Author-Year Format (AER Standard)

- Narrative: "Smith (2001) shows that..."
- Parenthetical: "...consistent with prior evidence (Smith, 2001; Jones, 2003)."
- Two authors: "Smith and Jones (2001)"
- Three or more: "Smith et al. (2001)"

### When to Cite

| Situation | Action |
|-----------|--------|
| Factual claim about the literature | Cite 2–3 representative papers |
| Methodological choice | Cite original methodological paper |
| Data source | Cite official documentation or published paper |
| Stylized fact | Cite the most authoritative source |
| Your own prior work | Cite it but don't over-cite |

### Literature Review Structure

The related-literature section organizes prior work into groups:
1. Papers that directly measure the same outcome
2. Papers that use a similar identification strategy
3. Papers that study a related mechanism

For each group: 1–3 sentences summarizing the group, then citations.
Don't summarize each paper individually — synthesize.

---

## 7. Response-to-Referee Patterns

### Point-by-Point Format

Structure the response letter as:

```
Dear Editor,

We thank the editors and referees for their careful reading. Below we respond
to each comment in turn.

---

**Referee 1, Comment 1**: [Quote or paraphrase the comment]

**Response**: [Your response]

[Changes made, if any, in italics]
*We added a paragraph in Section 3 explaining...*
```

### Positive Framing

- Acknowledge legitimate concerns directly: "The referee is correct that..."
- Never argue that a concern is invalid — either fix it or explain why you cannot
- "We agree that X is a limitation. We now acknowledge this explicitly in Section 5."

### Documenting Changes

After each response, state exactly where in the paper the change appears:
> "We have added the following text to the third paragraph of Section 2 (page 7):"
> [new text in italics or quotation marks]

### When You Can't Fully Address a Comment

Be direct: "We agree this would strengthen the paper. Unfortunately, [data constraint / 
identification reason] prevents us from implementing this. We have added a
discussion of this limitation in Section 6."

---

## 8. Anti-Patterns

| Anti-pattern | Better alternative |
|-------------|-------------------|
| "It can be seen that..." | State the result directly |
| "This is an important question" | Show *why* it's important (dollars, lives, policy) |
| Burying the contribution on page 3 | State the main finding in paragraph 2 of the intro |
| "This paper is organized as follows" as the last paragraph | Lead with findings, then the roadmap |
| Undefined notation at first use | Define every symbol immediately |
| "The coefficient is highly significant" | Report magnitude: "a 10% increase in X raises Y by $\hat{\beta}$ = 0.3 percentage points" |
| Passive voice throughout | Use active voice; say who is doing what |
| Hedging every claim | Hedge where genuinely uncertain; don't hedge standard results |
| Results-first without methodology | Always present model/identification before results |
| Inconsistent terminology | Fix one term for each concept and use it throughout |
