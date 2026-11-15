# Publishing with Press

Press holds works, editions and publisher configuration. Reusable software and its contracts live in [GuavaJam core](https://github.com/nashspence/guavajam/tree/main/projects/core).

- Start with `make setup`, `make help` and `make work`. Review generated material before committing.
- [Consumer contracts](tests/test_press.py) cover installed commands and workflow authority; [source CI](.github/workflows/validate-source.yml), [private qualification](.github/workflows/qualify-assets.yml), [maintenance](.github/workflows/maintain-assets.yml) and [public audits](.github/workflows/audit-source.yml) encode verification.
- `make capture` exports the installed extension. Native conversations and private review output stay outside tracked sources.
- [Core release contracts](https://github.com/nashspence/guavajam/blob/main/projects/core/tests/test_asset_release.py) define private staging and signed-main release.
- Supply signer trust independently. Publication requires the owner's deliberate signature; software installation never issues an edition.

Keep README and onboarding minimal. Tests define enforceable behavior; put rationale and verification history in issues/PRs. Delete task-created disposable resources after qualification.
