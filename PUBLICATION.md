# Publication policy

Only an edition issued through the [protected release workflow](.github/workflows/prepare-edition.yml) is official. The canonical HTML attached to its published GitHub Release is the citable text. Commits, bare tags, drafts, and prereleases are not editions. The workflow inputs and [publisher](scripts/publish_edition.py) define publication mechanics.

Before approval, review the built text, figures, and rights. Version changes are editorial decisions: normally start at `v1.0.0`; use major for a new edition, minor for substantive revisions, and patch for corrections. Preserve issued tags and artifacts. Describe corrections, supersessions, or withdrawals in the affected [GitHub Release](https://github.com/nashspence/press/releases) and any successor, rather than maintaining a second catalog.

Verify external identifiers against their issuing registries before recording them, including their exact work, edition, and format. The [registration validator](scripts/identifier_schema.py) defines accepted records; valid identifier syntax alone does not establish ownership.
