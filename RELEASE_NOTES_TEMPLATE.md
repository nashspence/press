# Official edition release-notes template

Copy the block below into a GitHub **draft release** and replace all placeholders before publication. The first four lines are checked by the release workflow.

```text
Work: [Full title]
Edition: v1.0.0
Canonical artifact: work-slug-v1.0.0.pdf
Rights: All rights reserved

## About this edition

[Summary or abstract.]

## Changes from the previous edition

[First edition, corrections, or substantive changes.]

## Alternate formats

[Optional additional attached formats, clearly distinguished from the canonical file.]
```

If assigned, include an additional section in release notes identifying the specific external registry records, for example a version DOI or ISBN for an attached format. **Omit unassigned identifiers.** Once the release is published, store verified registration facts in [REGISTRATIONS.md](REGISTRATIONS.md)'s edition record, including the final release asset SHA-256 digest. A concept DOI or author ORCID is not a substitute for an edition identifier.

The tag must have the form `works/<slug>/v1.0.0` and the named canonical artifact must already be attached before publishing. The release checker runs **after** publication, not as a pre-publication gate. See [PUBLICATION.md](PUBLICATION.md).
