# Compound GPID Editorial Brief Design System

Use this reference with `assets/editorial-brief-template.html`. The template is
the reusable implementation; this document explains which choices define the
visual identity and which choices should adapt to the content.

## Design Intent

The brief should feel like an editorial decision document built for careful
reading, not a marketing page or an application dashboard. It should make a
dense argument easier to scan without making it look simplistic.

The visual voice is:

- rigorous but not austere;
- warm but not decorative;
- bold in hierarchy, restrained in ornament;
- information-dense without feeling crowded;
- recognizable across subjects without forcing every subject into one layout.

## Core Tokens

Use these exact defaults:

```css
:root {
  --ink: #181816;
  --muted: #5d625f;
  --paper: #fbfbf8;
  --white: #ffffff;
  --line: #d8dcd8;
  --soft-line: #e9ebe8;
  --coral: #e94f2d;
  --coral-soft: #fff0eb;
  --teal: #087c70;
  --teal-soft: #e8f5f2;
  --blue: #2856c7;
  --blue-soft: #edf1ff;
  --yellow: #f2c84b;
  --yellow-soft: #fff8dc;
  --success: #18734c;
  --danger: #b8322a;
  --content: 1180px;
  --radius: 6px;
  --header-height: 64px;
}
```

### Color roles

| Token | Role |
|---|---|
| `--ink` | Primary text, borders, dark decision bands |
| `--paper` | Warm page background |
| `--coral` | Primary editorial accent, section signals, selected emphasis |
| `--teal` | Architecture and capability emphasis, positive structural signal |
| `--blue` | Rules, compatibility, and technical-system emphasis |
| `--yellow` | Kernel, sequence, and attention accents |
| `--success` | Pros and confirmed recommendations |
| `--danger` | Cons, forbidden dependencies, and material risks |

Do not turn the page into a single-hue theme. Coral, teal, blue, yellow, paper,
and ink should each have a clear job.

## Typography

- Display headings: `Georgia, "Times New Roman", serif`
- Body and controls: `"Trebuchet MS", "Gill Sans", sans-serif`
- Code and paths: `Consolas, "Courier New", monospace`
- Body default: `17px`, line-height `1.65`
- Hero title: approximately `76px` desktop, `43px` phone
- Section heading: approximately `46px` desktop, `34px` phone
- Panel/card heading: `26px` to `34px`, never hero-sized
- Letter spacing: `0`

Georgia carries authority and long-form editorial character. Trebuchet keeps
the body human and highly legible without looking like a generic product UI.
Use system fonts only so the file remains fully standalone.

## Geometry and Atmosphere

- Use square or lightly rounded corners. Keep radii at `6px` or less.
- Prefer 1px or 2px visible borders over soft shadows.
- Use offset hard shadows (`6px 6px 0`) only on diagrams and important framed
  structures.
- Use a warm paper background and a subtle 32px grid in the hero.
- Add narrow solid color bars at hero or decision-band edges.
- Avoid gradients, translucent color orbs, bokeh, glass cards, and nested cards.
- Use full-width section bands with a constrained inner width of `1180px`.
- Let white, pale green, and pale coral section bands alternate only when the
  information hierarchy benefits from it.

## Page Grammar

### Sticky header

Use a compact sticky header with:

- a small bordered brand mark;
- a short document-type label;
- anchor links to major sections;
- an optional `Print / PDF` button.

Hide secondary navigation on narrow screens. Keep the header at 64px desktop
and 56px phone.

### Hero

The hero is an unframed full-width field, never a card. Include:

- an eyebrow with date, status, or document type;
- a literal title naming the subject;
- a one- or two-sentence summary;
- compact metadata;
- one subject-specific visual summary when useful.

The hero should leave a visible hint of the next section in every supported
viewport. On phones, simplify dense visual summaries rather than stacking them
into an excessively tall introduction.

### Section heading

Use a two-column section head on desktop:

- a compact index such as `03 / Architecture`;
- a large heading and a muted one-sentence summary.

Stack these on mobile. Section indexes use coral unless another accent has a
strong semantic reason.

### Narrative plus evidence

For context sections, pair readable prose with a narrow evidence rail. Evidence
rails may include:

- large numeric metrics;
- short labels;
- one highlighted architecture signal or risk.

Use a drop cap sparingly for the first contextual paragraph. Never use it in
technical lists or compact panels.

### Requirement groups

Use an unframed two-column grid with a strong colored top rule for each group.
Do not put each requirement in its own card. Keep complete list wording and
allow natural vertical length.

### Conceptual diagrams

Use solid blocks, visible borders, and explicit labels. For layered
architectures:

- coral represents user-facing intent or suites;
- teal represents reusable capabilities;
- yellow represents the platform kernel;
- arrows or vertical connectors show dependency direction;
- a dashed danger note may identify forbidden edges.

Every diagram must also be understandable from nearby text and accessible
labels. Decorative geometry must not carry the only copy of a fact.

### Alternatives comparison

When approaches are present, always include two views:

1. A compact comparison table for orientation.
2. Detailed approach sections for fair evaluation.

Each detailed approach includes:

- approach number;
- title and effort estimate;
- one-sentence summary;
- enough explanation to understand how it works;
- complete pros and cons lists;
- recommendation or disposition.

Pros use a green `+`; cons use a red `-`. Display them in aligned columns on
desktop and in pros-then-cons reading order on phones. The selected approach
may use teal emphasis, but rejected approaches must remain fully legible.

### Decision band

Use a near-black full-width band with white text and narrow yellow/coral edge
bars. State the decision plainly in the heading. Follow with the rationale and
the disposition of alternatives.

### Rules and compatibility

Numbered rules work well as an unboxed list with circled numbers. Pair them
with a simple directional diagram when relationships matter. Compatibility
commitments use a strong blue accent and explicit, complete statements.

### Timeline

Use a vertical rule with numbered yellow markers. Each step gets a short title
and one explanatory paragraph. Do not turn every step into a floating card with
large whitespace.

### Open questions

Use a two-column ruled grid on desktop and one column on phones. Label each item
as an open question. Preserve the interrogative wording from the source.

### Footer

Use a dark footer with document identity, capture date, and compact topic tags.
Tags are metadata, not primary navigation.

## Responsive Contract

Use two primary breakpoints:

- `980px`: collapse major two-column narrative and decision layouts; simplify
  navigation.
- `720px`: stack section heads, requirements, tradeoffs, layers, and question
  grids; compact the hero visual; reduce title sizes.

At every viewport:

- stable controls and diagrams must have constrained dimensions;
- text must wrap without clipping;
- the page itself must not overflow horizontally;
- wide comparison tables may scroll inside a clearly bounded wrapper;
- reading order must remain logical when columns stack.

Validate at `390x844`, `1024x768`, `1440x900`, and `1920x1080`.

## Interaction Contract

Interactions are progressive enhancement only:

- thin scroll-progress line;
- smooth anchor navigation;
- active-section navigation state;
- restrained one-time reveal motion;
- print/PDF button.

Respect `prefers-reduced-motion`. Content must be visible without JavaScript.
Do not add carousels, hidden tabs, hover-only information, or interactions that
make the document harder to print or archive.

## Accessibility Contract

- Include a skip link and semantic `header`, `nav`, `main`, `section`, and
  `footer` landmarks.
- Use one `h1`, sequential heading levels, real lists, and real tables.
- Give diagrams concise accessible labels.
- Maintain visible keyboard focus.
- Do not use color as the only indicator; pair it with words, symbols, or
  structure.
- Ensure muted text remains legible against its background.
- Keep essential information in HTML text, not generated pseudo-content.

## Print Contract

- Hide sticky navigation, progress indicators, and print controls.
- Remove dark backgrounds when necessary for ink-efficient printing while
  preserving hierarchy with borders and typography.
- Avoid page breaks inside approach comparisons, layer diagrams, and timeline
  steps where practical.
- Force reveal content visible in print.

## Content Integrity

Design supports comprehension; it does not authorize summarizing away detail.
Before handoff, reconcile the HTML against the source:

- metadata values;
- every major heading;
- every requirement and constraint;
- every approach, effort, pro, and con;
- the exact chosen approach;
- dependency or governance rules;
- compatibility commitments;
- all next steps and open questions.

If the source repeats an idea, consolidate only when no qualifier or distinction
is lost.

## Anti-Patterns

Do not:

- build a generic SaaS dashboard for a narrative document;
- put every paragraph in a card;
- nest cards inside cards;
- use giant headings inside compact panels;
- rely on external fonts, icon CDNs, CSS frameworks, or JavaScript packages;
- use gradients or decorative blobs as atmosphere;
- hide rejected approaches behind accordions;
- show a pros/cons summary that omits source items;
- make the first viewport entirely metadata with no subject signal;
- require a development server for a standalone brief;
- claim browser validation without checking rendered desktop and mobile views.

## Final Visual QA

1. The first viewport names the subject, states the value of the document, and
   hints at what follows.
2. The palette uses all accents intentionally and does not read as one hue.
3. Headings fit their containers at phone and desktop widths.
4. No elements overlap or create page-level horizontal overflow.
5. Alternatives are equally understandable before the recommendation is read.
6. Pros and cons are complete, parallel, and easy to compare.
7. Diagrams agree with the prose and have accessible labels.
8. The page prints cleanly and opens directly with `file:///`.
9. External stylesheet, script, font, and image counts are zero.
10. The final artifact still contains every material fact from the source.