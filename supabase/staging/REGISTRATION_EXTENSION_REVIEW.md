# Tests2/3 exact-pair extension — prepared handoff only

Project hexhtduvqzleoazusskh, existing branch plan/security-remediation-2026-11-03. No staging SQL, Auth API login/signup/resend/verification, dispatcher, email, config/secret, function deployment, production, payment or cleanup is performed by this preparation. Only local disposable SQL/mocked app tests. User authorises reviewed development-branch push; not a main merge or deployment.

## Exact row-only addition

- Test2 d2598ebf-d44c-4e11-81a5-d82f3d06ada1 / urbanfolduk+staging-reg-02@gmail.com.
- Test3 3a4e8d72-bf58-468a-b24f-0417c4a64f5b / urbanfolduk+staging-reg-03@gmail.com.

011_registration_capture_extend.sql inserts ONLY these two enabled allowlist rows, with explicit server approval timestamps. It does NOT reinstall/reset010, change any function, create/alter tables/indexes/constraints/policies/grants, or change existing Test1 entry/approved_at. Old invalid-domain fixtures and exact-match protections remain unchanged. No Edge redeployment or secret change is necessary: existing capture function reads the private table dynamically. No wildcard Gmail/domain rules.

Guarded prerequisites: exact baseline marker/role; reviewed010 capture body hash a0a932e15140581b19189404dcb42d2d36190ce7bb3f27b4199b9ee9a84995c7, owner/definer/path/service-only ACL; expected four-column private allowlist PK/unique/FK/no client policies/grants/no unexpected triggers/rules; one exact enabled Test1 entry. Both new exact Auth identities must be confirmed and have canonical original/current false, one signup and verification audit each, one matching unclaimed pending registration event and zero receipts. Isolated pending queue must contain only these two. Unknown/already-extended/consumed state means STOP, no reset/upsert/overwrite.

The transaction locks the allowlist against competing writes and locks the two pending events against competing claims. Test1 row is snapshotted verbatim before/after. Registration/F02 events, receipts, canonical consent/audit, free allocations/purchases/revocations are compared unchanged within the transaction. Existing SQL source/security is only inspected, not replaced. No implicit notifications are requested. Pause any active automation with separate approval before future installation: do not rely on queue locks as a substitute for test scheduling.

## Files / review sequence

1. After separate read-only approval, connected reviewer verifies project reference and runs 011_registration_capture_preflight_readonly.sql. Expected before upgrade: entries1; Test1 allowlisted/accepted/one receipt; Tests2/3 not allowlisted, confirmed, false choices/consent, one signup/verification audit and one pending/zero receipts each. Compare capture hash, ACL/schema metadata and F02 baseline25 survey events/24 survey receipts/attempts. Preflight and postcheck use same SELECT-only query for before/after comparison; no raw Auth credentials or private message bodies returned.
2. Preserve actual metadata/Test1 entry/history and confirm no scheduler/other worker will run. With separate SQL approval apply ONLY011_registration_capture_extend.sql, not010/004/baseline. Fixed project ref must be independently verified: comment guard is not project attestation.
3. After separately approved installation run 011_registration_capture_verify_readonly.sql. Entries3, all exact pairs enabled; Tests2/3 still pending/zero captures, original/current false; Test1 row/history and capture hash unchanged; original RLS/service-read-only boundaries and F02 counts unchanged. 010 postcheck intentionally expects one entry and is not the correct postcheck after011.
4. No dispatcher call is authorised by this handoff. Later two controlled calls require explicit approval, secure narrow-secret invocation and queue/counter review. Existing claim code enforces atomic5/minute50/hour limits, terminal events not retried. Expected false checkbox/verified-consent payloads must be checked without treating a string true as consent; no actual Gmail email delivery (transport stays staging_capture).

## Rollback, separately approved only

011_registration_capture_rollback.sql verifies known source/private schema/exact three pairs and preserves snapshots, then disables ONLY Tests2/3 enabled flags. It deletes nothing, retains all three entries/approval timestamps/captured receipts/consent/history, leaves Test1 enabled and does not reinstall010 or replace functions. Repeat rollback is an idempotent no-op once both new rows are disabled. Unknown extra/mismatched entries or schema/source drift cause STOP. Never use010 rollback or008 cleanup for this row-only upgrade. Re-enabling requires a new separately approved exact-row operation; don't rerun the insert upgrade because it rejects three entries.

## Consent withdrawal readiness

See NEWSLETTER_WITHDRAWAL_TEST_PLAN.md and 011_newsletter_withdrawal_evidence_readonly.sql. Test1's generated signup password was not retained and no real Test1 session is available. No live authenticated withdrawal or impersonation is performed. A genuine valid Test1 session/normal-login credentials must be available before execution; no reset/admin session/token extraction. Control-user live session is also needed for the staging cross-user denial check. If unavailable, mark those managed tests blocked; local simulated role checks are not substitute proof of Supabase authentication.

Local tests model own-session RPC withdrawal, original/history preservation, one false audit and no duplicate on repeated false; other-user scope, forged target signature and direct DML denial. The live procedure leaves actual consent false and never erases audit or auto opts back in. Historical notification remains original true; future marketing must use current canonical false. Allowlist expansion/rollback does not change newsletter preference.

## Tests and residual limits

New SQL test includes valid upgrade/rollback; rejection on marker/source/grant/Test1/unverified/duplicate state; snapshots for all affected evidence; unchanged capture function; successful existing claim/capture/finish for both false-choice pairs; no service/client allowlist mutation. Code generation check prevents stale installer copies. Full local test evidence under audits/2026-11-06/registration-extension. New SQL fixture uses constants for approved test identities in network-disabled PostgreSQL only, no actual accounts changed.

Current database/SMTP/hook/queued state remains owner-reported, not independently queried during this task. Actual installation and rate/capture proof require later approvals and connected verification. Production, £6 credits and £179 service unchanged. Earlier uncommitted Security Advisor/self-signup investigation files remain outside this source handoff.
