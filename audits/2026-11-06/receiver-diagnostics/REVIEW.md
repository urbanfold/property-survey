# Receiver-only diagnostics — local development review

Date: 2026-11-06. Branch plan/security-remediation-2026-11-03. Base HEAD ac15c68d4f9d7521744eea2f062f9eff88ad6773; receiver changes are uncommitted/unpushed. Build: urbanfold-staging-receiver-diag-1. Source hashes: source-manifest.json. This work made no Supabase requests, deployments, secret edits, notifications, production calls, database migrations, credit changes, cleanup, commits, pushes or merges.

## Implementation

Only runtime changes are in the staging-only shared receiver and its regenerated single-file dashboard receiver. The fixed staging URL, server key authorisation, POST requirement, request validation, capture RPC and dummy-recipient enforcement by existing 005 SQL remain intact. Missing/empty/unrecognised mode now returns 503 before capture; exact valid modes remain accept/reject/timeout_after_capture. Setting read per invocation, with no trim/default fallback.

Structured log objects contain exactly component/build/event/mode. Modes are allowlisted or replaced by missing/invalid. Events are fixed internal strings. Logs include no raw invalid environment value, exception, request/header/body, correlation ID, recipient, survey content, token or key. Logs run only after project/server/method checks. Logger exceptions are swallowed to preserve notification behaviour. Capture-success and timeout-start/end markers bracket the unchanged real 12-second delay. Gateway and registration worker runtime code, database migrations, payment code, app.js, index.html and workflows match HEAD unchanged.

## Verification

21 new diagnostic tests cover shared and generated handlers; dashboard entry point is registered/executed through a Deno shim in Node. Exact generated/shared consistency also passes generator --check. Combined existing capture/registration CI entry point now imports the new tests, so the unchanged workflow runs them; combined result 29/29. Existing F02 gateway handlers 7/7; billing handlers 8/8.

Real timers, final combined run: shared gateway 10,021 ms / receiver 12,004 ms; generated gateway 10,022 ms / receiver 12,003 ms. Each test captured once, marked the mocked ledger uncertain and retained a dummy saved survey. After restoring the in-memory mode to accept, duplicate request returned uncertain without invoking capture again. HTTP, Auth, gateway RPC and receiver RPC calls were replaced in memory; no real account/endpoint used. This proves local JavaScript timing and integration, not managed Supabase runtime behaviour or deployed-source identity. Native Deno is not installed here.

All 18 final existing regression targets passed after the documented corrections/reruns: JS syntax, generator, billing, notification handlers, capture/registration handlers, registration SQL, newsletter UI, session teardown, session recovery, survey flow, browser photos/export, client allowance, Leica, RLS/storage SQL, £6 credit SQL, notification outbox SQL, payment-product isolation and staging setup structure. SQL tests use disposable network-disabled PostgreSQL; browser requests are mocked. See final-results.json and raw logs.

Initial failures retained:
- Four registration-worker tests already failed at base HEAD: request fixture used fixture-dispatch while configured secret was fixture-dispatch-token-32-characters. Reproduced against original test file (registration-baseline.log). Corrected two test request headers to reference the configured fake secret; no registration runtime changes.
- Adding diagnostic tests exposed a data-URL module-cache collision in the existing wrapper registration test. A test-only import fragment makes that wrapper register independently. Intermediate failed run retained as registration-final.log; corrected combined run passed.
- Leica browser test timed out locating Choose Leica device during parallel regressions. No application/test change; isolated rerun passed. Earlier intermittent failures were already documented; root cause not established. Raw initial/serial logs retained. A busy run also delayed Node timers; final uncontended timing shown above.

## Rollback provenance limitation

rollback-candidate contains byte-for-byte pre-change local shared/dashboard source and hashes. It is explicitly NOT a verified copy of currently deployed source. Owner confirmed deployed branch exists but has not supplied the entire active deployed source; management source/log access is unavailable. Requirement to preserve the exact deployed source remains blocked. Do not claim rollback export complete. Before deployment, owner must export/copy current staging receiver index.ts and any imports, record active version/JWT setting, and compare with this candidate. If identical, manifest hashes establish equivalence; if different, preserve exact exported files separately and review differences. No broad management credentials needed.

## Deployment checklist — NOT authorised or performed

1. Review this diff/results and complete the verified deployed rollback export above.
2. Obtain separate explicit staging deployment approval. Confirm Dashboard URL hexhtduvqzleoazusskh; do not use production. Confirm existing STAGING_RECEIVER_BEHAVIOUR=accept and NOTIFICATION_TRANSPORT=staging_capture without changing them. Snapshot reconciliation totals (23 events, 22 accepted, 1 uncertain, 22 receipts/attempts as last owner report); fresh metadata if time/activity has changed.
3. In Edge Functions > staging-notification-receiver > Code, replace only index.ts with supabase/dashboard/staging-notification-receiver.ts. Keep existing JWT verification setting (disabled with internal server auth); no gateway/worker/function additions, database SQL or settings edits. Deploy only this receiver after approval.
4. An unauthorised read/POST check may confirm 401 after approval. It cannot establish selected mode/build because diagnostics deliberately follow server auth. No broad service key in browser.
5. Obtain explicit testing/configuration authorisation for any new controlled dummy capture/timeout test. Use fresh saved fixture-6 revision; previously accepted content deduplicates and cannot validate new code. Confirm intended log mode/build before interpreting results. Restore accept before the duplicate check; reconcile exact events, receipts, attempts and saved survey.
6. Retain evidence; no cleanup or deployment to production implied by a staging pass.

## Rollback checklist — separate authorisation required

1. Stop new test submissions and restore staging behaviour to accept if fault mode was enabled, with permission for that configuration action.
2. Reinstall the VERIFIED pre-deployment receiver export in the SAME staging function, keeping the previous JWT setting. Do not change the gateway, schemas, credits, users or photos.
3. Confirm server-only unauthorised denial. Reconcile any receipts/events created before rollback; do not delete evidence or automatically resend uncertain notifications.
4. A source rollback does not undo captured receipts or reset uncertain events. Current known totals remain unchanged by this local work.

## Remaining risks

Explicit missing-mode rejection is intentional but can produce uncertain gateway events if misconfigured. Build identifier is a release label, not a cryptographic deployment attestation. No raw error details are logged, limiting root-cause visibility beyond safe phases. A process killed after capture may never emit timeout_wait_finished; receipt/event reconciliation remains authoritative. Custom log guarantees cover this handler, not every platform-managed log. Existing server-key trust and 005 dummy checks are preserved, not redesigned. Managed-runtime timeout/secret behaviour and current deployed source remain unverified. Preserve the working accept configuration until separately approved staging work.
