# Urbanfold-Survey-Staging — prepared setup, awaiting approval

**Nothing in this directory has been executed against any database. No function has been deployed. No GitHub connection, push, production setting or real customer data change is part of this preparation.** Stay on `plan/security-remediation-2026-11-03` / existing draft PR #1; these new files remain local until approved.

This is a reproducible reconstruction for a **fresh** Supabase project using current source requirements and historical diagnostic metadata. It is not a production clone and must not be called verified production parity. Start with [SCHEMA_INVENTORY.md](SCHEMA_INVENTORY.md), then review the SQL files themselves.

## Package and order

| Step/file | Purpose / boundary |
| --- | --- |
| `000_fresh_baseline.sql` | Creates seven original survey tables, explicit minimum table grants, RLS fail-closed, seven nonunique access-path indexes, three private buckets and a staging-only table comment interlock. Refuses existing Urbanfold tables/functions/buckets or Storage policies. Uses Supabase's real Auth/Storage, never the fixture. |
| `../001_secure_access.sql` | Unchanged owner/admin policies, property submission marker and path-based private Storage policies. Abort on unknown policies/public buckets. |
| `../002_survey_purchases.sql` | Unchanged £6 ledger, free allocation, server-only purchase/revocation functions and allowance/address triggers. Price and live/test credit rules preserved. |
| `../003_survey_notifications.sql` | Unchanged F02 private events/functions with deduplication and proposed caps. |
| `setup.sql` | Generated concatenation of the four sources in exactly that order, with source SHA-256 comments; includes no seed users/rows/files and executes no Edge Functions. |
| `metadata_readonly.sql` | Read-only catalog/bucket configuration snapshot for a separately approved comparison; no survey/Auth records or complete function bodies. |
| `verify_readonly.sql` | Read-only post-setup checks; all results should be true, followed by real-service tests below. |
| `seed_dummy_surveys.sql` | Optional, separate, one-time dummy A/B fixtures after new staging Auth accounts exist. Uses real owner RLS/free trigger. No real users/passwords/photographs. |
| `seed_dummy_credit.sql` | Optional, separate synthetic ledger simulation for seeded dummy A. No Stripe call or price/rule change; includes clearly synthetic test and live-flagged rows in staging only. Requires its own approval. |
| `test-photo.svg` | Synthetic image, no customer content or EXIF. Through the app it should be converted to JPEG; use it to test compression/uploads, or create a blank camera-test photo. |

The four files have separate transactions. 000 is **fresh-project-only, not rerunnable**: a second attempt stops before changes. 001–003 are existing repeatable source migrations; the bundle does not override their semantics. Do not use reset/drop-all commands. If a later step fails, earlier transactions can remain committed: stop, inspect metadata and approve a targeted continuation. Do not hide errors with `IF NOT EXISTS`, skip guards or blindly rerun the whole baseline.

The bundle is SQL Editor-compatible; a future psql execution must use `ON_ERROR_STOP=1`. Neither method automatically registers CLI migration history (`supabase_migrations.schema_migrations`). No CLI project linking or GitHub integration is required. If the team later adopts Supabase CLI migrations, map this exact sequence into timestamped migrations and review the ledger separately; do not mix manual execution with an unreviewed `db push`/`db reset`.

## Safe local preparation (text only)

These commands only generate/check files; they do not contact a database or execute SQL:

```sh
python scripts/build_staging_setup.py
python scripts/build_staging_setup.py --check
python tests/test_staging_setup_files.py
```

Do not run the existing database policy/credit tests as a way to apply this setup: they execute fixture SQL in disposable PostgreSQL and do not provision real Supabase. No SQL has been executed during this preparation, including in local containers. The prepared SQL still needs an approved database dry run and real-service checks; text checks cannot validate live DDL privileges/services.

## Approval gate before any SQL

1. Record the staging project's exact Dashboard URL/project reference from the owner and verify it is **Urbanfold-Survey-Staging**, not the original production project. The display name alone is not a unique identity. The reference is currently unknown to this preparation.
2. Confirm it is fresh, healthy, and contains no copied customers/Auth users/files/Stripe settings. Do not export/import production rows, auth.users, identities, passwords or Storage objects.
3. Review the schema reconstruction uncertainties and baseline index/grant differences in SCHEMA_INVENTORY.md. Approve staging-only execution of the exact SQL hashes. Production metadata comparison requires separate read-only approval and is not a reason to run writes there.
4. Use an explicitly selected staging SQL Editor session. The `urbanfold.staging_setup` acknowledgement and staging-only table comment are **operator interlocks, not proof of project identity**. Never paste this bundle into production. Original production app objects cause 000 to reject it, but operator target checking is still mandatory.
5. After approval only, execute the reviewed bundle with stop-on-error. If executing files separately, first set `urbanfold.staging_setup = 'Urbanfold-Survey-Staging'` in the baseline session, then run 000,001,002,003 in order. Stop on any error before creating dummy users or deploying functions.
6. Run verify_readonly.sql and metadata_readonly.sql in staging after separate approval. Review all false/null results and additional policies/grants. Do not loosen permissions simply to make a test pass.

## Auth and client configuration — manual staging-only work

- Create entirely new dummy A/B accounts in staging using Dashboard Auth tools or the staging signup flow, using `@example.invalid` addresses and unique generated passwords kept outside source/chat. Confirm these accounts administratively in staging if needed; invalid-domain addresses cannot receive email. Do not insert auth.users directly or copy real account UUIDs/credentials.
- Keep production Auth settings untouched. Record staging Site URL/redirects, confirmation/password settings and email-delivery setup. Testing actual confirmation/reset email delivery requires separately approved test inboxes/mail sink; invalid-domain dummy accounts cannot prove email delivery.
- The checked-in `app.js` still contains the production Supabase URL/public anon key. **Do not use the live Pages site for staging tests.** Prepare a separate, untracked staging client directory/origin after approval, replace only that copy's Supabase URL and public anon key with staging values, and label it STAGING. Never insert a service-role key. Check DevTools Network and require all Auth/REST/Storage/Functions traffic to hit staging; abort if production appears. Do not commit staging credentials or change Pages/main.
- Use a dedicated origin/browser profile so production session tokens/drafts cannot mix with staging; do not use production photo URLs even in dummy rows. For new Bluetooth tests use HTTPS on the Android tablet; a laptop's localhost secure-context exception does not make plain HTTP on a LAN tablet origin secure.
- Standard Authenticated/API tests require the project's anon key or compatible legacy public JWT key accepted by this vendored client, plus each dummy user's own bearer session. Server functions presently use legacy anon/service-role variables supplied by Supabase; confirm availability/compatibility rather than copying production values.
- The existing admin email `urbanfolduk@gmail.com` is hardcoded in app/RLS/ledger/F02. No real admin account is copied/seeded. A genuine staging admin UI test is **blocked pending an approved test identity strategy**: either explicit permission to create a new staging-only identity for that address, or a separately reviewed, consistent staging-only admin-identity substitution. A SQL claim simulation is not proof of real Auth admin access. Do not silently substitute or register the real address.

## Dummy data / photographs

Choose either app-created dummy surveys or the optional seed, not both for the same users: each account has one initial free survey. The seed requires NEW staging Auth UUIDs in session settings and rejects users who already have surveys/free allocations. It sets a dummy authenticated role/claims only inside the transaction to exercise the actual owner policies; those SQL simulations do not replace real bearer-token/API tests.

For photos use the staging client/Storage API, not SQL inserts into storage.objects. Test each category:

| Category | Bucket / required object prefix | Reference table |
| --- | --- | --- |
| Front/rear/side exterior | exterior-photos / `<property UUID>/...jpg` | exterior_photos + elevation_type |
| Extension position/inspiration | exterior-photos / `<property UUID>/...jpg` | extension_photos |
| Floor-layout sketch | sketch-photos / `<property UUID>/...jpg` | sketch_photos |
| Room photograph | room-photos / `<property UUID>/...jpg` (not room UUID) | room_photos + room_id |

Use unique random filenames; app compression uploads JPEG. No real homes/people/customer plans are needed. Bucket size/MIME limits remain NULL as in the historical diagnostic, pending a separate compatibility/hardening decision; F06 is not solved by private ownership alone. Remove-photo tests should remove database references while retaining private bytes, matching the app's current behaviour. No Storage UPDATE/DELETE policy is added for an operation the app does not perform.

## F02 Edge Function and secrets (prepare now; deploy only after approval)

Deploy exactly `request-survey-notification` from `../functions/request-survey-notification/index.ts` and `_shared/notifications.mjs`, or equivalent generated `../dashboard/request-survey-notification.ts`. Verify parity with `python scripts/build_dashboard_functions.py --check`. Root config records `verify_jwt=false`; this is intentional because the handler validates the caller through Auth itself. That validation and caller-token/RLS property read must remain enabled.

| Server variable | Staging-only value / boundary |
| --- | --- |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | Normally platform-injected **staging** values; verify without logging/copying secret values. Never use production service-role credentials. |
| `APP_URL` | Approved staging HTTPS client URL; notification origin compares scheme/host/port, not URL path. Billing additionally requires a trailing slash. Never leave the production fallback for staging tests. |
| `SURVEY_NOTIFICATION_WEBHOOK_URL` | A **new test-only Zapier catch URL**, with no real customer sends. Handler validates HTTPS hooks.zapier.com `/hooks/catch/`; an arbitrary localhost receiver will not pass unchanged code. Test Zap should capture data only, or use an approved dummy inbox. Do not copy production webhook credentials. |

Payload: property_id, client_email, address, surveyor_name and server-derived submission_id. Confirm actual intended recipient/templates using dummy data; saved client contact need not match a professional's login email. Recipient consent/control is not proved by survey ownership. Caps remain 20/account and 5/property/day; retention/reconciliation need decisions. Leave the production exposed webhook working until its replacement is fully tested and separately approved for retirement.

## £6 payment backend — no live Stripe work

The database setup already installs the unchanged credit rules. Keep payment functions undeployed/disabled initially. If later approved for staging sandbox integration, use existing `create-survey-checkout` and `stripe-survey-webhook` modules/dashboard equivalents and root verify_jwt=false configuration. Checkout validates Auth; webhook validates raw Stripe signatures.

Additional server variables: `SURVEY_PAYMENTS_MODE=disabled` initially, then only `test` with a **new staging/sandbox** `STRIPE_SECRET_KEY` (`sk_test_...`) and a **new sandbox destination** `STRIPE_WEBHOOK_SECRET`. No production keys/destination or real card/payment. Mode disabled also rejects webhook processing; document it when testing failures.

Sandbox purchases are recorded with `live_mode=false` and **do not unlock additional surveys** under the existing rules, even in a separate staging project. Do not change that behaviour. Test checkout/signature/dedup/cancel/refund separately from redemption. The optional dummy-credit seed creates clearly synthetic ledger rows in the empty staging database (including one live-flagged synthetic row) solely to exercise unchanged redemption; it never calls Stripe and is not a genuine purchase. Obtain explicit approval for this simulation. Never mutate a real test payment to live or advertise synthetic rows as revenue. £179 Essential Feasibility is not part of any staging credit test.

## Real-service verification matrix after approval

Record pass/fail plus expected/actual HTTP status, actor, dummy IDs and deployed staging version; redact tokens/secrets. Prefer Authenticated API requests as well as UI checks. Do not conclude RLS works from an admin SQL Editor or service-role client.

1. Catalog checks: all 11 tables/RLS, explicit grants, private buckets, trigger definitions and seven helper signatures/settings/ACLs; compare inventory to metadata. Verify public is Data API-exposed, but ledgers/helpers still inaccessible as specified.
2. A and B can each sign in and view/edit their own property; A cannot select/update/delete B's parent or any child, move a child to B, or assign a property to B. Anonymous public table access must fail (permission error is acceptable, not necessarily zero rows). Owner cannot change ownership away from self.
3. A uploads all four categories to A's prefix; B's attempts to upload/list/sign/download A's objects through authenticated requests fail; anonymous signing/public URL fails. Test spoofed prefix and both old/new reference parsers with **staging** URLs only. A copied, valid signed URL is a bearer link until expiry; do not misinterpret that as a fresh B-authorised signature. Confirm no extra permissive storage policies.
4. Known F04: inserting an own-row reference that names another property's file can still succeed; its object must remain inaccessible. Record this as the existing unresolved integrity issue, not a silently passing strict URL-binding test. Also review nullable parent columns/no extra NOT NULL checks against metadata.
5. Save/reopen every section, rectangular/L-shaped rooms, Hallway/Landing, photos, JSON/ZIP/PDF exports and reset flow; compare cloud data from a fresh session. A real admin export test awaits the admin identity decision above.
6. Exercise F01 on real staging Auth: deliberate warning/cancel/save/logout, no old DOM; same-user token/email refresh preserves edits; offline entry/save failure retains work; unexpected expiry locks/hides, temporary snapshot not persisted, same-ID fresh access required, B cannot recover, revoked access denied, delayed callbacks cannot restore old user data, cross-tab logout, tab-close warning limitations. Leica needs approved HTTPS/tablet staging origin and reconnection after lock.
7. Credit rules: first free allocation, no second property without usable credit, edits free, concurrent creation, failed insert rollback, submitted address lock. Sandbox test payments must not unlock; optional synthetic staging live row grants exactly one, redemption consumes it once, duplicate record unchanged, unused revoked credit denied. Admin exception and refund/dispute real sandbox integration are separate checks. No £179 path should mint £6 credit.
8. F02: no session/unconfirmed actor/wrong owner/body tampering denied; saved submission marker required; fresh dummy submission gives one dummy receiver event; duplicate/concurrent/unchanged content stays one; changed content/rate caps, receiver rejection, timeout and receipt-write failures show uncertainty without repeated sends or lost-survey claims. Verify professional→different dummy client contact.
9. Do not call staging complete until all required real-service checks pass or blockers are explicitly documented. Local mocks/PostgreSQL fixtures cannot certify Supabase Auth, Storage, email or deployed API isolation.

## Stop/rollback rules

This is additive fresh staging setup, not a production rollback plan. If a step fails, stop and inspect committed metadata; do not drop/reset schemas, delete Auth users, disable RLS, broaden grants or reconnect to production. No teardown/cleanup script is included. Approve any later staging recreation separately after confirming its unique project reference. Production F01/F02 rollout and rollback remain governed by the existing deployment checklist and separate approval.

## Outstanding inputs / approval

- Exact staging project reference and staging client origin, reviewed baseline deviations and permission to execute the four SQL sources.
- Optional read-only production metadata comparison, especially FKs/delete actions, ACL/default grants, indexes, helper bodies/settings and trigger parity.
- Staging-only dummy Auth/account confirmation plan, admin test identity, test email/notification receiver and later sandbox Stripe configuration if required.
- Approval for Edge Function deployment/secrets, optional dummy seeds/synthetic credits, real service tests and eventual push to the existing branch/PR. Nothing here authorises production or GitHub integration.
