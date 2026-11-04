# Asset custody

Keep an independent backup of each original. The [asset helper](scripts/prepare_asset.py) defines the exact content-addressed key and response headers; consult `make help` for commands. Upload unchanged bytes to the public B2 bucket under that key with those headers. The native B2 API requires encoding the cache directive as `X-Bz-Info-b2-cache-control`. Keep credentials outside Git. Do not overwrite or expire referenced objects.

Configure the public gateway using the inputs required by the [deployment script](scripts/deploy_asset_gateway.py), review its plan before applying it, and inspect the [live Markdown preview](storage/README.md). Keep retained copies of published edition artifacts and the original image bytes. Decide Object Lock and retention policy operationally; no storage provider is a permanent archive by itself.

To restore or migrate, recover the original bytes from backup, a retained object version, or a verified published edition. Verify the SHA-256 against the content-addressed URL before restoring the same object key. Preserve the public hostname and old origin through a verified cutover; run the [integrity audit](.github/workflows/audit-assets.yml).
