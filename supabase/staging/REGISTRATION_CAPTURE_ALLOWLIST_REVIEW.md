# Exact registration capture exception — local review, not deployment

Target: Urbanfold-Survey-Staging hexhtduvqzleoazusskh ONLY. Approved identity: b83f87d8-abf2-4800-beab-8279917804c7 / urbanfolduk+staging-reg-01@gmail.com. No SMTP credentials, password, token or verification link is in these sources. No Supabase SQL, deployed function, dispatcher invocation, email, config, payment, merge or cleanup was performed during preparation.

## Why SQL is necessary

The Edge receiver has no email-domain check: it forwards server-authenticated data to public.capture_staging_notification(). The original 005 SQL enforces @example.invalid. Changing only Edge code would still reject this valid-domain self-registration. The functional change is therefore the restricted SQL allowlist. Edge code changes only its non-sensitive build marker to urbanfold-staging-receiver-allowlist-1 and documents SQL as authority; auth/project/mode/HTTP/capture/diagnostic/timeout behaviour is identical. No new endpoint, environment variable, secret, registration dispatcher or gateway change is required.

## Exact scope

010 creates public.staging_registration_capture_allowlist with exactly one enabled user/email pair, RLS on, no client policies or client grants. Owner administers entries; service_role can SELECT but cannot INSERT/UPDATE/DELETE. Nothing is configurable by a browser/user_metadata/header. Arbitrary Gmail addresses/domains are not allowed.

For the added valid-domain case, capture requires all of: exact allowlist pair enabled; exact actual Auth user/email and confirmed state; delivery UUID bound to that user's real registration event; state sending/accepted/uncertain with server claim timestamp; matching payload event ID, registration/verification timestamps, historical checkbox and verification opt-in values; fixed admin recipient and correct notification type. Pending events cannot bypass the existing rate-limited claim path. Current preference withdrawal does not change the historical notice or require opt-in for a service notice.

Legacy invalid-domain registration capture remains as before for existing dummy fixtures. The survey branch is byte-for-byte equal to 005 and still requires DUMMY property, invalid-domain client and actual invalid-domain Auth owner. approved_registration is false for every survey call, so Gmail exception cannot leak into F02. No changes to Auth/consent/notification queue rows, surveys/photos or £6 credits are made by installing010.

Idempotency remains the receipt PK(kind,delivery_id). A direct service-role retry updates attempts, not another receipt row, as in005. The unchanged dispatcher claim logic never reclaims terminal events, and atomic5/minute50/hour dispatch limits remain unchanged. Capture is not real email delivery; receiver has no sending code and transport must remain staging_capture.

## Files

- Shared/complete dashboard receiver: supabase/functions/_shared/staging_receiver.mjs and supabase/dashboard/staging-notification-receiver.ts.
- Complete guarded SQL proposal: supabase/staging/010_registration_capture_allowlist.sql.
- SELECT-only pre/post checks: 010_registration_capture_preflight_readonly.sql and 010_registration_capture_verify_readonly.sql.
- Guarded rollback: 010_registration_capture_rollback.sql.
- Generator: scripts/build_registration_capture_sql.py (--check compares, never executes SQL).
- Tests: tests/test_registration_capture_allowlist.py plus updated receiver diagnostics. Existing registration SQL CI command includes the new allowlist test.

## Review and future installation/deployment sequence — separate approval

1. Use a read-only connected review of the identified staging project. Run010 preflight only with permission: original capture source hash must equal capture-body-hashes.json's original005 hash; owner postgres/SECURITY DEFINER/empty search_path and service-only execution; no existing allowlist; exact verified Auth identity; one pending approved event, zero approved registration receipts. Compare against004 queue/canonical consent metadata. Unknown capture source/previous allowlist/nonpending/consumed event means STOP, no overwrite/reset.
2. Confirm no active scheduler, webhook, Auth hook or other worker is automatically invoking the registration dispatcher. If automation is active, pause it only with separate approval BEFORE adding the exception. Installing010 does not itself invoke a function, but active automation could consume the pending event as soon as the rule permits it. Initial tests must be manual only.
3. Preserve actual deployed capture function definition/ACL/owner and active Edge source/version/JWT settings privately. Existing local diag-1 snapshot is only a repository rollback candidate until compared with the active deployed export. Guard hashes normalise line endings and outer whitespace only. Check actual connection ref: marker comments are not independent project attestation.
4. Obtain separate SQL installation approval; apply ONLY010 allowlist SQL, not005 or the historical baseline. It is one transaction and rejects reruns/unknown source. It creates one allowlist row and replaces only capture function's registration check. It sends nothing and does not claim/finish a queued event. Explicit function ACLs remain public/client denied, service execute. No001–004, credits or Auth setting changes.
5. Run010 postcheck SELECT: four allowlist boolean checks true, helper hash matches new reviewed hash, server-only permissions maintained, original F02 survey totals25 events/24 receipts/24 attempts unchanged, registration receipts still0. No permissive RLS policies just to silence the intentional no-policy allowlist warning.
6. Edge redeployment is NOT functionally required: current receiver calls the same RPC and will use new SQL immediately. If reviewing the updated build marker too, obtain separate deployment approval and replace ONLY staging-notification-receiver index.ts with the generated dashboard file, preserving verify_jwt=false and internal auth. No secret changes. Unauthorised browser still401. Build marker alone cannot attest SQL deployment; postcheck hash is authoritative.
7. Verify REGISTRATION_NOTIFICATION_TRANSPORT=staging_capture and STAGING_RECEIVER_BEHAVIOUR=accept via permitted secure configuration review. Do not change secrets or SMTP. New Gmail address is only captured notification DATA; no Gmail/Brevo/SMTP/Zapier delivery occurs. Auth's Mailtrap confirmation path is separate.
8. Obtain explicit one-call dispatcher approval and a secure server invoker with the existing narrow dispatch secret (not customer JWTs or exposing the service key). Ensure the pending queue contains only the approved test event to avoid consuming another user's notice. Expected one registration receipt/attempt, event accepted, historical true choice. Preserve survey receipt counts by kind. No dispatcher call is authorised by this source review.

## Rollback / emergency restriction — separate approval

- Stop authorised test invocations; if automation exists, obtain approval to pause it first. If provider transport/fault mode changed independently, restore only approved staging settings; this patch requires no such changes.
- After approval run010 rollback: requires the same staging marker/role AND reviewed new capture body hash. It restores verbatim005 function body and server-only EXECUTE grants, not a broad schema reset. Unknown intervening function changes cause STOP. Existing receipts, attempts, consent, queue, Auth accounts, allowlist table/row and F02 evidence are retained. Once restored, the Gmail registration capture is denied again.
- Rollback deliberately does not delete/disable the allowlist row: old005 no longer consults that table. Do not drop the table or run008. Reinstalling after rollback needs a separately reviewed upgrade because the fresh installer refuses an existing table. Any later allowlist expansion/revocation is an exact-identity owner-only operation requiring approval, not a wildcard/config fallback.
- If desired, restore the verified pre-deployment Edge source/version separately, preserving JWT/internal auth. A SQL-only rollback is sufficient to remove this capture exception; Edge build change has no delivery behaviour.
- Source rollback cannot undo a captured receipt or un-send an external email (none is implemented here). Do not reset accepted/uncertain events or automatically retry them. Preserve evidence and reconcile by event UUID/kind.

## Tests / remaining limits

All tests are local: mock HTTP or disposable PostgreSQL with --network none; the approved live test identity is represented by constants in an isolated fixture, never queried or changed remotely. Tests cover denied identities/domains, unclaimed/unconfirmed/mismatched events, tampering, allowlist privacy/no service writes, stable consent/credit/F02 installation snapshots, historical consent after withdrawal, receipt PK/attempts, source/marker guards and data-preserving rollback. Full regression results and hashes are in audits/2026-11-06/registration-capture-allowlist.

No actual installation, effective deployed ACL, confirmed capture for this account, Mailtrap/Gmail delivery, live rate-limit run or native Supabase source version is certified by local tests. Future actual preflight/approval is required. No exception for unchecked/invalid test accounts is included; any future identities need exact approved pairs and separate change review.
