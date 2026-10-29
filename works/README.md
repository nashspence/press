# Works

This directory contains **working sources**, not automatically published editions.

For each work, create a folder named with a lowercase hyphenated slug, such as `works/example-essay/`. Copy all files from [templates/work/](../templates/work/) into it and update the manuscript title and metadata to match the slug. See the mandatory [format specification](../FORMAT.md).

A v1-compliant layout is:

```text
works/
  example-essay/
    README.md         # optional editorial notes
    manuscript.md     # canonical working source
    metadata.json     # required canonical metadata
    assets/            # optional local PNG/JPEG/WebP/passive SVG
```

Commits and folders are always working history. For published editions, see the [catalog](../CATALOG.md) and [publication protocol](../PUBLICATION.md).
