# Manuscript source format

This document defines the **machine-checkable** source conventions for Press. The repository's publication authority is defined separately in [PUBLICATION.md](PUBLICATION.md).

## Source format

- All tracked `.md` and `.markdown` files use **UTF-8**, **Unicode NFC**, **LF** line endings, no byte-order mark, and a final newline.
- Manuscripts use **GitHub Flavored Markdown (GFM)** with dollar-delimited TeX math, and are compiled as `gfm+tex_math_dollars+raw_html` by **Pandoc 3.12.1**. GitHub supports related Markdown/math features, but its rendering engine and Pandoc are not identical.
- Write meaningful textual symbols as real Unicode (`§`, `¶`, `→`, `∞`, `∀`, `∈`, `∎`), not font-dependent symbols or images. Use TeX in math contexts (`$x \in S$`), not manually arranged ASCII approximations.
- Use ATX headings (`#`, `##`, etc.); use a single level-1 title in each `works/<slug>/manuscript.md`; do not skip heading levels.
- Put a stable anchor before every level-2 or deeper manuscript heading. Explicit anchor names must be unique in each file and match lowercase hyphenated identifiers such as `sec-1`, `def-1`, `thm-2`, and `proof-2`.
- Preserve **semantic structure**: sections use headings; figures use Markdown images with descriptive alt text; notes use `[^note-id]`; cross-references use Markdown links to stable IDs.
- Local Markdown links and image paths must resolve in the checked-out repository. External URLs and site-root URLs are not tested for reachability.
- Display math uses `$$` delimiters on their **own lines**, paired within a manuscript. Inline math uses `$...$`. TeX expressions are rendered to HTML5/MathML in CI.
- Work directories are named with lowercase ASCII slugs (`works/<slug>/`), and use `manuscript.md` for the main source.

## Example

```markdown
# On Structure and Identity

<a id="sec-1"></a>
## § 1 — Foundations

Let $S$ denote the set of admissible symbols.

<a id="def-1"></a>
### Definition 1.1 — Identity

$$
\forall x,y \in S,\quad x \sim y \iff f(x)=f(y)
$$

See [Definition 1.1](#def-1).
```

## Validation and publication

Run `python3 scripts/validate_sources.py` locally with Pandoc on your `PATH`, or rely on `.github/workflows/validate-source.yml` on pushes, pull requests, and manual runs. The workflow checks **all tracked Markdown files**, not just changed ones. CI checks encoding/normalization, manuscript headings/anchors, basic math delimiter pairing, image alt text, local file/section links, Pandoc parsing, and an HTML5/MathML render smoke test. The Python test suite is also run in CI.

These are **structural and build checks**, not a proof of mathematical correctness, complete TeX support, link longevity, HTML accessibility, typographic quality, or identity between GitHub's renderer and Pandoc. They do not themselves create an official release. Generated HTML, styling, Pages deployment, license compliance, and release artifacts need their own build/release checks when those systems are added.

To actually **require** a passing check before merging, configure branch protection or a repository ruleset for `main` and require the **Validate manuscript sources** job. A workflow by itself only reports failures.
