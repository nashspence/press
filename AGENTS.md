# Publishing with Press

Press holds works, editions and publisher configuration. Reusable software and its contracts live in [GuavaJam core](https://github.com/nashspence/guavajam/tree/main/projects/core).

- Start with `make setup`, `make help` and `make work`. Review generated material before committing.
- [Consumer tests](tests/test_press.py) cover this repository's dependency and commands; [CI](.github/workflows/validate-source.yml) validates source and assets.
- `make capture` exports the installed capture extension. Native conversations and private review output stay outside tracked publication sources.
- [Asset maintenance](.github/workflows/maintain-assets.yml) owns this publisher's operational gates. `make asset-credentials` creates its local credential template.
- `make site-template` drafts publisher-owned settings; review, commit and sign the checkpoint separately.
- Supply signer trust independently of the source repository. Publication requires the owner's deliberate signature; software installation never issues an edition.

Keep README minimal and this onboarding short. Tests define enforceable behavior. Put rationale and verification history in issues/PRs. Delete task-created disposable repositories and hosting resources after recording qualification results.
