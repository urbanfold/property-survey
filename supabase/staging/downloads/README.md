# Local staging client download

This ZIP is a generated, local-only staging test client, not a deployment. It contains no entered key/password or production Supabase endpoint/public key. Configuration targets only hexhtduvqzleoazusskh. Source/limitations: ../client-tools/README.md and scripts/build_staging_client.py.

Archive integrity checked. SHA-256: `20afd01e092509db561e1aefe14ee2dbab4dfe921fbf33bd3df6a5b4c07b3b29`. Windows launcher remains unexecuted on the Linux preparation host; generated browser tests used intercepted HTTP.

Prepared as a fallback for ChatGPT artifact download failure. Do not push until the owner approves this branch update. No merge or production deployment is authorised. After an approved push, use the ZIP file's Download raw file button in GitHub.

Version 2 adds a read-only account-isolation button; no DevTools console pasting is needed. It checks unfiltered property IDs and a direct other-dummy-property request under the current dummy session. Mocked tests cover A/B success, denied/incomplete results and simulated API leaks. It does not test writes/photographs or certify live isolation.
