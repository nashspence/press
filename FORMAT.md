# Press source format — v1

This is the **normative** authoring contract for the `press` repository. [`scripts/validate_sources.py`](scripts/validate_sources.py) is its executable reference; [`tests/test_validate_sources.py`](tests/test_validate_sources.py) contains passing and failing examples. [`PUBLICATION.md`](PUBLICATION.md) separately defines what constitutes an official edition.

## Manuscript format

- Author in **UTF-8, NFC-normalized Unicode, LF line endings**, no BOM, no trailing spaces, exactly one terminal newline. The validator rejects selected invisible text controls and bidirectional overrides. Meaningful prose symbols (e.g. `§`, `¶`, `→`, `∀`, `∈`, `∎`) are literal Unicode; mathematical notation uses LaTeX math.
- Manuscript path: `works/<slug>/manuscript.md`, where `<slug>` is lowercase ASCII letters/digits separated by hyphens. Only `manuscript.md`, `metadata.json`, `README.md`, and files inside `assets/` may live in a work directory under v1. Expanding the source format requires an explicit policy change.
- Markdown dialect: **Pandoc GFM reader** `gfm+tex_math_dollars+raw_html`, **Pandoc 3.12.1**. This is a reproducible *profile* of GFM, not a promise that GitHub's HTML renderer is byte-identical to Pandoc. Pandoc parsing and HTML5/MathML rendering must complete **without warnings**.
- Use `#`-style ATX headings only. Each manuscript has **exactly one H1 title**, the first heading. Heading levels cannot be skipped. Every H2–H6 heading is preceded by a standalone `<a id="stable-id"></a>` (immediately or across one blank line), with a unique lowercase ASCII stable ID. The validator rejects stray anchors, unsafe raw HTML, and collisions with generated heading IDs.
- Cross-references use Markdown links (`[Definition](#def-1)`). Local links must resolve to **tracked** files, and fragments in Markdown must resolve to a section ID. Absolute repository-root links and local query strings are rejected. External links are allowed only with `https:` or `mailto:`. External images are prohibited in manuscripts.
- Images must use Markdown syntax and descriptive alt text, and their referenced assets must live under the **same work** at `works/<slug>/assets/`. Allowed formats: PNG, JPEG, WebP, and passive SVG. Images are limited to 10 MiB each; SVG scripts, external references, inline CSS, and embedded active content are prohibited. SVG may contain shapes/text/paths.
- Use `$...$` for same-line inline math and `$$` **alone on lines** for display math. Escape literal currency dollar signs as `\$`. The validator rejects unmatched delimiters, and verifies that Pandoc recognizes exactly the expected number of math expressions and renders them as MathML.
- Use GFM footnotes `[^note-id]` with a matching unique definition. Unused, missing, and duplicate definitions fail. Use standard Markdown lists, blockquotes, code fences, tables, and emphasis as appropriate. Unpaired code spans and unclosed fences fail.
- Raw HTML inside manuscripts is **not** allowed except the exact standalone stable section anchors above. This protects canonical semantics and avoids GitHub/Pandoc rendering divergences.

## Mandatory metadata

Each `works/<slug>/manuscript.md` requires `works/<slug>/metadata.json` in **canonical JSON** (UTF-8 NFC, keys sorted alphabetically, 2-space indentation, final LF; duplicate or extra keys fail). All seven keys are required, all values are strings:

```json
{
  "author": "nashspence",
  "language": "en",
  "rights": "all-rights-reserved",
  "schema": "press.work.v1",
  "slug": "sample-work",
  "status": "draft",
  "title": "Sample Work"
}
```

The `title` must equal the rendered plain-text H1; `slug` must equal the work folder; `status` is always `draft` in working sources. **Official publication status belongs to releases, never metadata in the source tree.** `language` is a two- or three-letter lowercase language code, optionally followed by a two-letter uppercase region. `rights` is one of `all-rights-reserved`, `CC-BY-4.0`, `CC-BY-ND-4.0`, `CC-BY-NC-ND-4.0`, `CC0-1.0`. Granting a license still requires valid applicable rights and edition-specific release declarations.

## Example manuscript

```markdown
# Sample Work

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

## Enforcement and scope

Locally, install **Pandoc 3.12.1** and run:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_sources.py
```

[The source-validation workflow](.github/workflows/validate-source.yml) runs both against the entire tracked tree on pushes, pull requests, and manual dispatch. A failing check is informative until the repository's `main` branch has an **active ruleset requiring the `Validate manuscript sources` check and pull-request merges**. Protect the ruleset from bypass as appropriate, and protect publication tag names against deletion/updates. Workflow/validator changes must receive the same scrutiny as manuscript changes.

This checker guarantees **compliance with the stated syntactic profile**, not correctness of mathematical propositions, factual citations, readability, internationalization, copyright permissions, external URL availability, or arbitrary GitHub-renderer parity. It checks generated HTML for basic semantic structure and MathML, not visual responsiveness or full accessibility. GitHub Pages deployment, finalized artifacts, SHA-256 provenance, and *pre-publication* release gating must be specified and enforced separately; the existing `check-release` job is post-publication only.
