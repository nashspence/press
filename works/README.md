# Works

This directory contains **working sources**, not automatically published editions.

For each work, create a folder named with a lowercase hyphenated slug, such as `works/example-essay/`. Copy the files from [templates/work/](../templates/work/) into it, then update the YAML front matter in `manuscript.md`: its `slug` must match the folder and its `title` must match the H1. See the mandatory [format specification](../FORMAT.md).

A v1-compliant layout is:

```text
works/
  example-essay/
    README.md         # optional editorial notes
    manuscript.md     # YAML front matter + canonical working source
    assets/            # optional local PNG/JPEG/WebP/passive SVG
```

Commits and folders are always working history. For published editions, see the [catalog](../CATALOG.md) and [publication protocol](../PUBLICATION.md).
