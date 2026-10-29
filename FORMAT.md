# Press source format — v1

This is the **normative, executable authoring contract** for `press`. [`scripts/validate_sources.py`](scripts/validate_sources.py) enforces this contract, with positive and negative regression cases in [`tests/test_validate_sources.py`](tests/test_validate_sources.py). [`PUBLICATION.md`](PUBLICATION.md) separately defines which GitHub Releases constitute official editions.

## Manuscript source and metadata

Each work lives in `works/<slug>/manuscript.md`, where `<slug>` consists of lowercase ASCII letters/digits separated by hyphens. **All work metadata lives in that manuscript's YAML front matter. There is no `metadata.json`.** The only other permitted work files under v1 are an optional `README.md` and local image files in `assets/`. Every work directory must contain its manuscript.

A manuscript begins **at byte zero** with a `---` line, a flat YAML mapping, a closing `---` line, exactly one blank line, and then the Markdown body. The block is limited to 128 lines. All seven required fields must be present, with no other fields. Order is free. All values must be nonempty **single-line YAML strings**:

```markdown
---
schema: press.work.v1
title: On Structure and Identity
author: Nash Spence
slug: structure-and-identity
language: en
status: draft
rights: all-rights-reserved
---

# On Structure and Identity

<a id="sec-1"></a>
## § 1 — Foundations

Let $S$ be a set, and let $x \in S$.

<a id="def-1"></a>
### Definition 1.1 — Identity

$$
\forall x \in S,\quad x=x
$$

See [Definition 1.1](#def-1).
```

### YAML restrictions

- The YAML must be a **flat mapping of keys to one-line string scalars**; multiline (`|` / `>`), nested mappings, sequences, flow collections, anchors, aliases, merge keys, custom tags, and directives are prohibited. Human-readable comments and quoted string values are allowed. Use quotes for values YAML might treat as booleans, dates, numbers, or null.
- Duplicate keys, missing keys, unknown keys, malformed YAML, and empty values fail. Keys do **not** have to be alphabetically sorted; this is an authoring format, not a serialized database record.
- `schema` must equal `press.work.v1`; `slug` must match the directory name; `title` must **exactly match the rendered plain-text H1** in the manuscript body; `author` must be nonempty.
- `status` must equal `draft`. Publication status is determined exclusively by qualifying GitHub Releases, never by manuscript metadata.
- `language` accepts lowercase two- or three-letter codes with optional uppercase region, such as `en` or `en-CA` (syntactic check only, not a full BCP 47 registry lookup).
- `rights` is one of `all-rights-reserved`, `CC-BY-4.0`, `CC-BY-ND-4.0`, `CC-BY-NC-ND-4.0`, or `CC0-1.0`. Publication licensing still requires the rights holder's authority and unambiguous edition-specific declarations.
- The validator uses **PyYAML 6.0.3** for syntax and scalar-type checking and independently confirms that **Pandoc** reads the same fields with the same values. Syntax accepted by one parser but interpreted differently by the other fails.

## Markdown and symbols

- Use UTF-8, NFC-normalized Unicode, LF line endings, no BOM, no trailing whitespace, and **exactly one terminal newline**. Selected invisible text controls and bidirectional overrides are prohibited.
- The declared manuscript dialect is **Pandoc 3.12.1** using `gfm+tex_math_dollars+raw_html+yaml_metadata_block`. This is a specific, testable profile of GitHub Flavored Markdown, **not** a promise that the GitHub website renderer is byte-identical to Pandoc.
- Use literal Unicode for meaningful prose symbols (e.g. `§`, `¶`, `→`, `∀`, `∈`, `∎`) and LaTeX notation within `$...$` or display math.
- Use ATX (`#`) headings only. Each manuscript has exactly one H1 (the first heading); levels cannot skip. Each H2–H6 heading needs a unique standalone `<a id="stable-id"></a>` immediately before it or separated by one blank line. Other raw HTML is prohibited.
- Use Markdown cross-reference links to stable IDs, e.g. `[Definition](#def-1)`. Local links must resolve to **tracked files**; fragments in Markdown must resolve. Local query strings and root-absolute paths are prohibited. External links may use `https:` and `mailto:`, but external images are not allowed in manuscripts.
- Image alt text is required. Images must be in the same work's `assets/` directory; supported formats: PNG, JPEG, WebP and passive SVG, at most 10 MiB each. SVG scripting, external references and other active content are prohibited.
- Inline math uses paired same-line `$...$`; standalone display delimiters `$$` must each be on their own line and paired. Escape literal currency dollar signs as `\$`. Pandoc must parse exactly the expected math objects and emit MathML for each.
- GFM footnotes `[^note-id]` require unique definitions and references; unused, missing and duplicate definitions fail. Standard GFM lists, blockquotes, tables and fenced code are allowed; unmatched code spans or code fences fail.

## Validation and scope

CI runs on every push, pull request and manual dispatch, checking all tracked sources, not just modified paths. With **Pandoc 3.12.1** and **PyYAML 6.0.3** installed, run locally:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_sources.py
```

The validator verifies front-matter semantics and Pandoc metadata parity, source structure, links, assets, parsing without warnings, and HTML5/MathML rendering. The render check suppresses Pandoc's automatic *second* visible title heading so the body retains its single H1. This does not yet specify a finished HTML design/template or deploy GitHub Pages.

A failing GitHub Actions check is informative until an **active repository ruleset protects `main` and requires the `Validate manuscript sources` check**, with bypass settings configured appropriately. Source checks cannot prove the validity of mathematics, factual assertions, authorship/rights, external URL availability, full HTML accessibility, or browser visual parity. Official-release gating and immutable asset provenance are separate stages in [`PUBLICATION.md`](PUBLICATION.md).
