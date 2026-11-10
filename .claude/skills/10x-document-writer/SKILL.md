---
name: 10x-document-writer
description: Create or revise Lumen Health case-study documentation as clear, standalone HTML using the red-forward 10X Health theme from codex/executive-summary.html. Use for reports, architecture notes, briefs and executive summaries in this repository.
---

# Lumen Health case-study document writer

Create documentation for this case study in a consistent visual style based on [the executive summary](../../../codex/executive-summary.html).

Use this skill when writing or updating a case-study document in this repository.

Name Lumen Health as the fictional company in the brief. Use 10X Health only when referring to the recruiter or the hiring process.

Keep the requested output format. Use HTML when the user wants a styled document, and keep Markdown when the user explicitly asks for Markdown.

## Theme

Treat `codex/executive-summary.html` as the source of truth for the theme and inspect it when exact styling matters.

Use the restrained 10X Health palette, with red as the primary accent and blue reserved only for a distinct meaning that cannot be shown clearly with a neutral:

- Brand red: `#c00000`.
- Deep red for links and hover states: `#980000`.
- Pale red for callouts and selected states: `#fbeaea`.
- Ink: `#202427`.
- Muted text: `#62686d`.
- Rules and dividers: `#dedede`.
- Pale page background: `#f5f5f5`.
- Neutral code or secondary flow: `#737373`.
- White surfaces: `#ffffff`.

Use the system sans-serif stack `ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`.

Use charcoal text, light heading weights, compact uppercase eyebrow labels, subtle grey rules and restrained red accents.

Use the brand red for the page rule, eyebrow, links, recommendation callout border and small section accents.

Use pale red fills sparingly for selected information and callouts.

Use neutral greys for code paths or secondary diagram categories so red remains the clear brand accent.

Avoid blue in page chrome, links, labels, table headers and decorative diagram elements.

Keep body copy comfortable to read at about `15px` with a line height near `1.5`.

Style `h1` around `37px` at weight `580` with tight negative tracking, and section headings around `16px` at weight `580` with modest negative tracking.

Use the summary's white letter-sized page, generous margins, thin section dividers, pale red recommendation panel, simple role chips and restrained footer as starting patterns.

For longer documents, extend the same colors and type hierarchy across a scrollable page and multiple printed pages.

Do not compress long content into a one-page layout unless the user asks for a one-page deliverable.

## HTML document practices

Make HTML documents standalone, responsive and printable, with embedded CSS and no required external fonts, scripts or network assets.

Use semantic headings, sections, lists, tables and links.

Give diagrams accessible labels and descriptions; prefer inline SVG when a diagram materially clarifies the document.

Keep every section at the same hierarchy level as a sibling unless it is intentionally a subsection.

Close each section before opening the next one; accidental section nesting can progressively narrow the page content.

Use responsive rules for narrow screens and print rules for letter-size pages where appropriate.

Maintain visible keyboard focus for links and controls, and preserve readable contrast.

Keep visual decoration secondary to the content. Do not add cards, gradients, shadows or animation unless they fit the restrained reference style and improve comprehension.

## Case-study evidence and language

Preserve the distinction between facts established by the supplied code, observations from the supplied CSV snapshot, design recommendations and open questions.

Label vendor names such as Shopify or Salesforce as inferred unless the brief or production evidence confirms them.

Do not present the local CSV replay as a production REST service or claim that production transports are known.

When the document discusses health information, state design assumptions plainly and identify production privacy, contract and legal details that require confirmation.

Use examples and identifiers from the fictional case data only when they help explain the model, and do not introduce real personal or health information.

## Completion

Before finishing, check that internal links resolve, the heading hierarchy is coherent, sections are not accidentally nested and print styles do not clip content.

Tell the user which file was created or updated and note any important assumptions or preview limitations.
