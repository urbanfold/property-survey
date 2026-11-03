# Local preparation status — 3 November 2026

Prepared on `plan/security-remediation-2026-11-03` after approved F01 commit `2ea131a`. Draft PR #1 is preserved. This staging package is local only, not pushed. No SQL (including local container SQL) has been executed, no Supabase connection made, no function deployed, no secret copied/configured and no staging GitHub integration added. Production application/Pages, Supabase, Stripe and customer data are unchanged.

## Checks performed

- `python scripts/build_staging_setup.py --check` — PASS: generated sequence matches the exact four source files and their SHA-256 hashes.
- `python tests/test_staging_setup_files.py` — PASS: text-only 11-table reconstruction, original-table column/FK fixture parity, fresh-object guards, explicit GRANT/RLS declarations, three private-bucket declarations, £6/600-pence contract, separate dummy seeds and read-only query boundaries.
- `python scripts/build_dashboard_functions.py --check` — PASS: existing generated function files unchanged/current.
- `git diff --check` — PASS.

No database-semantic, managed-service, end-to-end staging Auth/Storage/email, real Stripe sandbox, RLS or SQL execution tests are claimed by these checks. Existing application tests were not rerun because this change does not alter application/backend runtime code, and the SQL tests execute SQL that the owner has not yet approved for this stage.

## Proposed changes / compatibility decisions

Adds a fresh staging-only baseline, using the seven original table column definitions, inferred PK/FK relationships, minimum API grants, enabled RLS, seven nonunique supporting indexes and three private buckets. Root migrations 001–003, billing/notification handler implementations and F01 client remain byte-for-byte unchanged. Existing sources are embedded in the generated bundle, not forked into independently edited migrations.

The baseline rejects existing Urbanfold objects and does not drop/reset data or recreate Supabase-managed Auth/Storage. It records a staging-only comment interlock for optional dummy seeds. This and the acknowledgement are not cryptographic verification of project identity: the owner/operator must verify the exact staging project reference before approval/execution.

NULL bucket size/MIME limits preserve historical configuration; later hardening needs separate review. Seven added nonunique staging indexes and narrower original-table grants are explicit reconstruction choices, not statements of exact production parity. Known F04 reference-to-object integrity and existing admin-email model are not silently changed.

## Open approvals / inputs

1. Unique staging project reference and approved staging-only client origin, checked against the production endpoint before connecting.
2. Review/approval to apply the exact baseline + 001 + 002 + 003 sequence to staging; optional read-only production metadata comparison first if desired.
3. Real staging baseline compatibility: FK actions, current extra columns/constraints/indexes, effective/default grants, RLS/policies, function bodies/owners/settings, triggers, API exposure and managed Storage ACLs all require verification before claiming production accuracy.
4. New dummy Auth identities, confirmation strategy, admin test identity decision, dummy photographs and a new test-only Zapier receiver; no real Auth users/passwords/photos/hooks copied.
5. Separate approval for staged Edge Function deployment/server secrets, optional synthetic credit seed and real-service verification. Stripe remains disabled unless separately approved for sandbox-only integration. Test Stripe payments do not unlock live credits under unchanged rules.
6. Report/review these files before any push to the existing branch/PR or any SQL execution. Production rollout remains separately prohibited without explicit approval.
