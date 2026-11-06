# Isolated staging status — recorded 4 November 2026

## Known target and evidence

- Staging: **Urbanfold-Survey-Staging**, reference **`hexhtduvqzleoazusskh`**.
- Dashboard: https://supabase.com/dashboard/project/hexhtduvqzleoazusskh . This is the owner-supplied staging identity, not an independent project API inspection.
- Original production reference: `arnzqizcycesukplmvuc`. Never use it for these tests, seed scripts or staging client configuration.
- The owner approved staging setup and supplied screenshots of successful `setup.sql` completion and **12/12 true** `verify_readonly.sql` results. The schema is already installed on that evidence; the fresh-project installer is not the next step.
- Those metadata checks establish reported configuration results, not end-to-end real Auth/RLS/Storage isolation, exact production schema parity or F02 delivery.
- No staging connection to GitHub has been reported; none was added by the assistant. No function deployment, staging sender configuration, test receiver, dummy identities, dummy-data inserts or paid credit tests have been confirmed to the assistant.

## Complete reviewed database sequence

The exact table/column/FK/index/constraint inventory is `SCHEMA_INVENTORY.md`; authoritative source text is in the following files:

1. `000_fresh_baseline.sql`: seven original tables — properties, extensions, rooms, exterior_photos, extension_photos, sketch_photos, room_photos — explicit grants, enabled RLS, supporting nonunique indexes and three private buckets.
2. `../001_secure_access.sql`: owner/admin row policies and private object-prefix SELECT/INSERT policies, plus properties.last_submitted_at.
3. `../002_survey_purchases.sql`: survey_free_allocations, survey_credit_purchases, survey_credit_revocations; unchanged 600-pence/GBP rules and free-credit/address-lock triggers/helpers, plus address_locked.
4. `../003_survey_notifications.sql`: survey_notification_events and service-only claim/completion helpers. Does not deploy the Edge Function or configure secrets.

Together: **11 public application tables**, **7 SECURITY DEFINER helpers with fixed search paths**, **2 property triggers**, and **3 private buckets**. Bucket names are exterior-photos, sketch-photos and room-photos; extension-location photographs share exterior-photos. Object keys begin with the property UUID, including room photographs. Owners may access only their own parent/child rows/objects, apart from the existing signed admin-email exemption. The original survey tables have no anonymous app grants; notification events/service helpers are not browser-accessible. Storage bytes are uploaded through its API, never direct SQL inserts.

No migration/DDL/runtime change is proposed by this status update. £6 app credits remain separate from £179 Essential Feasibility. Test-mode Stripe purchases must not unlock live credits; no production Stripe or email credentials are needed. F02 still requires `request-survey-notification` deployment and staging-only SUPABASE variables, APP_URL and a new test-only SURVEY_NOTIFICATION_WEBHOOK_URL as detailed in README.

## First staging step for review — no SQL execution

**Reuse and inspect the existing staging project, not the fresh installer.**

1. Open the staging Dashboard link above; verify project name/reference before navigating further. Do not use a saved production SQL Editor tab.
2. In **Table Editor**, inspect that the 11 named application tables exist; do not add/edit rows. In **Storage**, inspect that the three named buckets are private; do not upload production photos or change policies.
3. Review `SCHEMA_INVENTORY.md` against the supplied 12-check screenshot. Earlier checks did not establish every FK/delete action/index/function body or production parity. Any further metadata SQL is a separately reviewed next step, not something run by this update.
4. Determine whether the two previously requested staging-only dummy Auth accounts already exist before creating duplicates. Their UUIDs have not been supplied. No passwords/API keys should be sent in chat. A new test-only client must point to staging; the current live Pages app points to production and must not be used for staging tests.

This first step performs no SQL, imports, migrations, user creation, function deployment, GitHub push/merge or application publication. Do not rerun setup.sql/000 or reset/drop anything.

## Remaining gates

- User-reviewed exact production metadata (optional read-only approval) before claiming parity: columns/defaults, FK actions, constraints/indexes, effective/default grants, RLS/policies, helper signatures/owners/settings/definitions, triggers and bucket limits/ACLs.
- New/confirmed dummy Auth A and B, with staging-only confirmation strategy; admin test identity needs an explicit decision because the application/source policies retain a fixed existing admin email. Do not copy a real Auth user.
- An isolated staging client origin and staging public anon key setup, with network inspection proving no production calls; never a service-role key in the client.
- Real dummy-owner cross-account read/write/photo signing/upload denial tests, cloud recovery/F01/exports/Leica checks, and separate notification/backend checks after approved deployment.
- A new dummy notification receiver and staging-only sender/test inbox configuration if testing real email delivery. Production Brevo credentials/settings are not staging configuration and must not be copied.
- No production writes, merges, deployment, secret rotation or live Stripe changes are authorised by resuming staging preparation. This documentation update is local only.

## Dummy identity update — owner-supplied IDs

A (`staging-owner-a@example.invalid`): `d72b4323-d71b-4b87-b78a-09896647fddf`. B (`staging-owner-b@example.invalid`): `9036b71c-4f09-4d1b-9dce-519533c4001e`. The owner supplied two distinct UUIDs; the assistant has not verified them through an Auth connection. No passwords or keys were supplied.

`seed_confirmed_dummy_users.sql` is a local, configured copy of the optional dummy seed. It additionally requires the exact A/B email-to-UUID mapping and confirmed emails, retains the staging marker/empty-allocation guards, and creates no paid credits or external calls. No seed execution result has yet been received. Do not rerun setup.sql; run the configured seed once only in the identified staging project, stopping on any error. SQL claim simulation is not real user/API isolation verification.

## Corrected dummy mapping from Auth screenshot

The first configured seed failed its exact email/confirmation guard before any survey INSERT. Read-only results showed both accounts exist and are confirmed but neither matched its assigned email. The owner’s Auth screenshot establishes the corrected mapping:

- A, `staging-owner-a@example.invalid`: `9036b71c-4f09-4d1b-9dce-519533c4001e`.
- B, `staging-owner-b@example.invalid`: `d72b4323-d71b-4b87-b78a-09896647fddf`.

This supersedes the earlier owner-supplied A/B labels above. Only the two settings in the configured seed were corrected; staging/email/confirmation/empty-allocation guards remain intact. No SQL was executed by the assistant and no account was altered. After correction the owner may run the complete configured seed as a new staging query; do not rerun the baseline. No successful seed result has yet been received.

## Dummy seed completion and local client preparation

The owner supplied the expected completion screenshot after correcting the A/B settings directly in the SQL Editor. This is user-provided evidence that the two dummy properties/free allocations were created; no paid credits were added. Do not rerun either the baseline or seed. The assistant did not execute cloud SQL.

A separate local-only client ZIP has been prepared under `/workspace/urbanfold-staging-client.zip` using `scripts/build_staging_client.py`; see `client-tools/README.md`. The user enters the staging public key only into that local screen, not chat or repository. No public key/password/secret was supplied to the assistant. The original live client files and all production services remain unchanged. Generated-client Chromium tests passed with all HTTP intercepted; actual staging login, cross-user API/storage denial, email/functions, admin exports and Windows launcher behaviour remain to be verified by the operator. No new code was pushed or deployed.

## Operator login evidence and no-console read check

The owner supplied screenshots of successful local staging A login showing only dummy A, then B login showing only dummy B. These establish owner-reported login/dashboard switching, not proof of RLS beyond UI filters. The attempted Console read test was blocked by browser paste protection and did not execute. Test tools v2 adds an on-page read-only button instead; no browser protection changes are needed. Mocked generated-client tests pass for A/B success, API leak detection, permission/error not passing, no REST mutations and cleared results on logout. No successful real on-page property-read check has yet been received. Production remains unchanged.

## Direct cloud staging tests completed

The owner published environment settings and the assistant directly verified real A/B Auth, unfiltered/direct property isolation, selected write restrictions, private photo uploads/signing/listing/download denials, unchanged free/600-pence allowance, actual browser save/reload/photo export and F01 recovery with simulated session loss/offline transport. Dummy records were restored; tiny private synthetic Storage bytes remain under current retention semantics. Detailed scope/evidence: [STAGING_RESULTS.md](/workspace/property-survey/audits/2026-11-04/STAGING_RESULTS.md). This supersedes earlier unperformed-test statements only for these tested staging paths. Production remains unverified/untouched. F02 gateway returns 404 and requires approved staging deployment/test receiver; no notification or Stripe work was performed.

## Phase 2 current boundary

See [PHASE2_REPORT.md](/workspace/property-survey/audits/2026-11-04/PHASE2_REPORT.md) and F02_PHASE2_PLAN.md. New capture-only receiver (005), registration/consent schema (004), dispatcher and optional schedule (006) are prepared/tested locally only. Current dummy credentials cannot deploy; actual new endpoint/table probes remain 404. No cloud SQL/functions, live receiver, Brevo or Stripe change was made in this phase. The original A/B fixtures remain untouched by these read-only probes. Root staging setup.sql remains the historical 000–003 baseline; do not rerun it or assume it installs new optional features.

## Deployed F02 negative checks

Owner reports 005 installation/security checks and both capture-only function deployments completed. Direct authenticated deployed boundary tests now pass; see `audits/2026-11-04/F02_DEPLOYED_STAGING_RESULTS.md`. This supersedes previous endpoint-404 status for these two functions only. Successful capture/duplicate/rate/fault tests remain blocked on dedicated fixtures and owner-only count access. Prepared (not executed): `007_f02_dedicated_test_fixtures.sql` and `f02_read_only_counts.sql`. No production changes, additional deployments, pushes or credit changes.

## Dedicated F02 endpoint phase

Owner reports 007 installed with six fixtures and zero starting events/receipts. Direct tests now exercise accepted requests, sequential/concurrent duplicates, changed submissions, five-per-property and twenty-per-actor cap responses, reserved-domain receiver guard rejection and saved-data preservation. Original A/B property hashes and allowance responses matched before/after. Private counts remain unverified; expected totals are 22 events (21 accepted, 1 uncertain), 21 receipts, 21 committed capture attempts. Run `f02_positive_read_only_evidence.sql` to reconcile. Configured timeout/reject modes require a manual staging-only setting change; not performed. No cleanup or push. See updated F02_DEPLOYED_STAGING_RESULTS.md and timestamped JSONL evidence.

## Timeout attempt — 2026-11-06

Owner confirmed timeout_after_capture saved. One dedicated B/fixture-6 revision/request was made. Unexpected HTTP 200 accepted in 2.303 seconds, so timeout verification FAILED to exercise the fault. No retry; saved fixture and original B property hashes matched. Operator instructed to restore accept and reconcile counts; cause unknown pending configuration/deployed-source review. Evidence: audits/2026-11-06/F02_TIMEOUT_STATUS.md. No cleanup, push, merge, deploy or production change.

## F02 survey staging verification PASSED — final reconciliation

Owner confirmed final 25 events / 23 accepted / 2 uncertain / 0 sending, 24 captured receipts / 24 attempts / zero repeated captures. Owner logs confirmed diag-1 real timeout sequence and no receiver capture during exact-revision duplicate; accept restored. Direct request/readback evidence retained. See audits/2026-11-06/F02_STAGING_VERIFICATION_PASSED.md for scope and production limits. This supersedes earlier pending-reconciliation status, not the unperformed production tests. Cleanup008 not run.

Registration 004/dispatcher/consent/scheduler reviewed without SQL, deployment or messages; plan and gaps in audits/2026-11-06/REGISTRATION_NOTIFICATION_REVIEW_PLAN.md. No numeric dispatch cap and no claim timestamp/stale-sending recovery currently implemented; local targeted changes require separate approval. Registration staging is NOT marked passed. Future receipt counts must separate survey and registration_verified kinds.

## Registration implementation completed locally for committed-source handoff

Root004 and generated dispatcher now include atomic 5/minute + 50/hour caps, server claim timestamps, safe stale-sending recovery to uncertain, exact-claim/persisted-state completion and fixed-field privacy diagnostics. Existing confirmation-state/strict consent/withdrawal/no-backfill rules preserved. Guarded fresh-only installer, SELECT-only pre/post verification and acknowledgement-guarded trigger-only rollback pause are prepared and tested locally. Source/test review and approval boundaries: REGISTRATION_RELEASE_CHECKLIST.md and audits/2026-11-06/registration-implementation/REVIEW.md. All 18 local regression targets passed, combined handlers 34/34. No Supabase SQL/functions/settings/accounts/emails or cleanup executed in this implementation. Connected Supabase reviewer must check metadata and obtain installation approval separately; no registration staging pass or production release is implied.
