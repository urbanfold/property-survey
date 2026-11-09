# Production backend installation review — 7 November 2026

**REVIEW PUBLICATION ONLY. Not approved for SQL execution or production release. No Supabase SQL, deployment, secret change, email, payment, merge or evidence cleanup was performed.**

Pinned development source: **5d434a78ac1f997c86b9c92646771de2018cad04**. Intended production project: **arnzqizcycesukplmvuc**. Staging hexhtduvqzleoazusskh must remain separate and its notification transports disabled. This package is published to the development branch only for independent inspection; the pinned canonical migrations/handlers are unchanged. The accompanying results.json records the earlier local preparation stage, before publication; its committed_or_pushed=false value is historical evidence, not the current publication status.

## Evidence and current decision

**Reconciliation update:** production findings and supplied trigger/default/dependency metadata are reviewed in [RECONCILIATION_REPORT.md](RECONCILIATION_REPORT.md). Only the exact extensions width/length numeric(5,2) compatibility exception is added to10/20. Original00 and its baseline fingerprint are unchanged. Next proposed SQL is the separately reviewed SELECT-only01, not an installer; observed10fa... remains unapproved. No production schema correction or001/002 replay is proposed.

Owner/connected ChatGPT reports production healthy, three private photo buckets, properties/credit RLS, two active payment functions, absent003/004 tables/functions, disabled leaked-password protection and no migration history. Those facts do NOT establish exact001/002 definitions, policies, grants, constraints, trigger behaviour, function versions, webhook delivery or production parity. This development agent has not inspected production database metadata directly. Final deployment remains BLOCKED pending the SELECT-only preflight and independent comparison.

Do not repeat the passed staging registration, withdrawal/idempotency, recovery or F02 tests. Genuine second-user newsletter authorization proof remains a separate release gate unless the connected reviewer has now obtained it; never impersonate a user with SQL claims/admin credentials or resubscribe Test1 to manufacture a test.

## Review files and order

| File | Purpose / authority |
|---|---|
| `01_reconciliation_readonly.sql` | Supplemental SELECT-only precision/FK/non-row grants/roles/automatic-RLS/watcher metadata after the first00 result; no installation. |
| `RECONCILIATION_REPORT.md` | Owner-supplied production findings, exact benign fixture differences, narrow guard exception and unresolved evidence gates. |
| `00_preflight_readonly.sql` | First action for separately authorised connected reviewer: SELECT-only existing metadata, source-model reference, function body/security checks, new-object collisions, baseline fingerprint. No customer/Auth rows, secret values or full function bodies. |
| `reference_001_002.json` | Offline PostgreSQL17 fixture + pinned001/002 source model: required columns, exact policies, expected constraints/indexes. NOT production metadata. No recommendation to copy fixture grants. |
| `source_spec.json` | Canonical001–004 file hashes, 14 reviewed helper signatures/body hashes. Body comparison normalises CRLF/LF and trims outer whitespace, never strips SQL/comments. |
| `10_install_003_fresh.sql` | Guarded fresh-only003 body, transactionally wrapped. Execution prohibited until independent metadata review/approval. |
| `20_install_004_fresh.sql` | Guarded fresh-only004 body;003 must already exist. New Auth triggers activate recording on commit; review their dependencies first. |
| `30_postinstall_readonly.sql` | SELECT-only existing-baseline digest, all14 function hashes/ACLs, four new table permissions/RLS, policies, constraints/indexes and two exact Auth trigger definitions. Run after each stage and interpret only objects expected at that stage. |
| `40_disable_auth_recording.sql` | Separately approved emergency pause ONLY if new Auth recording breaks signup/confirmation. Two exact named triggers, no drops or data repair. |
| `41_enable_auth_recording.sql` | Separately approved resume after verified fix and an inventory of the recording gap. No backfill or inferred consent. |
| `50_registration_schedule_review.sql` | LAST, separately approved scheduling action. Can cause future real emails. Requires reviewed Cron/pg_net/Vault and explicit delivery acknowledgement. No extension install or secret provisioning. |
| `51_schedule_verify_readonly.sql` | SELECT-only schedule flags after Cron installation; does not execute it or expose its full command/secrets. |
| `SHA256SUMS.txt` | File integrity inventory; metadata/source review is still required. |

Reproduce/check the main prepared files with `python -B scripts/build_production_backend_review.py --check`. Local test `python tests/test_production_backend_review.py` uses disposable network-disabled PostgreSQL only; it never connects to Supabase. Optional `--prepare-reference` regenerates the source model locally, not production metadata. Trigger recovery and scheduler files are separately reviewed templates, not regenerated by this builder; local tests parse/exercise them with inert cron/net stubs.

## 1. Identify the real production connection and preserve current state

- Connected reviewer confirms the actual Dashboard/integration project is arnzqizcycesukplmvuc, healthy, using trusted postgres/no simulated JWT claims. The custom SQL acknowledgement is NOT server identity verification. Never point a CLI default/linked project at production by assumption.
- Save authorised schema-only exports of existing tables/constraints/indexes/policies/grants, function/trigger definitions, active Edge versions/JWT settings, current Pages commit/artifact, scheduler/default-privilege metadata and provider settings through protected channels. Do not put secrets or real customer records in GitHub/chat.
- Confirm a usable database backup/restore process for the current plan. A schema export cannot restore customer data. A full database restore is a last resort requiring separate approval and a reconciliation plan for writes since backup.
- Record existing Stripe endpoint/version and working Zapier workflow before change. No Stripe configuration or payment function change is currently proposed.
- Use one operator and no concurrent schema/function/provider changes for the reviewed window. SQL uses a shared transaction advisory lock and short lock/statement timeouts; this does not coordinate arbitrary third-party DDL. New FKs/Auth trigger DDL can briefly block active writes; review an appropriate low-traffic window. Do not silently increase timeouts if a lock fails.

## 2. Run only00 preflight; determine whether001/002 need any correction

Review `deployed_001_002_metadata` against `reviewed_reference_001_002` and the pinned sources. Missing migration history is not permission to replay migrations. Do not run `supabase db push`, baseline000, staging setup.sql, reset or ledger backfill.

Required review:

1. All seven survey/photo tables and all three credit tables, their required columns/types, null/default behaviour, PK/FK/unique/check constraints, validated constraints and indexes. Credit checks must preserve exactly600p/GBP, session and intent uniqueness, one lifetime free allocation, one-time redemption and revocation bookkeeping. Additional legitimate columns/indexes are not automatically an error; determine their meaning. Missing required constraints or incompatible differences require a separate targeted proposal; the reconciliation report explains why existing cascading FK rules are preserved.
2. Exact owner/admin policies on every property/child/photo table, two Storage policies, own credit SELECT policies, and absence of extra permissive policies. All ten existing tables plus storage.objects must have RLS; all three buckets private. Metadata includes policies/grants; table RLS alone is insufficient. Confirm effective authenticated app read/write and own credit-read grants as well as anonymous denial. Do not blanket-copy fixture grants or remove legitimate provider policies blindly.
3. All five002 functions present with source-matching bodies, correct argument names/types and return types from the canonical source, trusted owner, SECURITY DEFINER/fixed empty search path, authenticated-only allowance RPC and server-only purchase/revocation access. Trigger helpers need no customer EXECUTE. Any fingerprint mismatch beyond line endings/outer whitespace needs private definition comparison; body hashes do not prove header/argument parity by themselves.
4. Both properties triggers present/enabled, call the reviewed functions at the correct events, and no unexpected property/Auth/DDL trigger or external side effect. Preflight returns hashes rather than raw trigger arguments/function bodies because legacy definitions may contain secrets. Review unexpected source privately, including dependencies/dynamic SQL. Understand any automatic RLS helper before DDL. Enumerated dependencies/hashes cannot prove absence of every possible external action.
5. Global/schema default ACLs and inherited client roles. The new installers abort on effective unexpected client grants before commit, but do not silently rewrite project-wide defaults. Other unexpected grants need individual review.
6. New target tables/function names/overloads/reserved Auth trigger names MUST be absent. If anything exists, STOP; no replace/reset/reinstall path is authorised.

**Decision:** if actual001/002 are equivalent, preserve them and install only003/004. If not, identify exact differences and prepare a separately approved targeted correction; regenerate/re-review guards where a genuine semantic formatting/type difference demands it. Do not run001 (policy drops/replacements) or002 (allocation backfill/address-lock updates) just to create migration history. Do not write guessed historical migration-ledger entries.

The installer deliberately requires exact source-model policies and existing002 helper bodies, required columns/types, enabled credit triggers and private/RLS prerequisites. Policy formatting/version or harmless structural differences can produce STOP; review and adjust the narrow proposal rather than bypass the gate. The approved fingerprint binds remaining deployed metadata (including reviewed constraints, existing triggers, defaults and grants) to the reviewed state; it is not a substitute for reviewing it.

Save the `baseline_sha256` in the release evidence ONLY AFTER the entire actual comparison/dependency review is accepted. It contains metadata, not customer rows; no full-table data scan is needed. Record this as a manual migration reconciliation/release inventory with source hashes, approval and later execution timestamps; no automated migration history is asserted.

## 3. Approve and install only the new database migrations

No SQL is to be executed during this preparation. Future installation needs separate approval of exact scripts/source hashes and connection identity.

For each of10 then20, edit ONLY the two parameter literals after approval:

- `urbanfold.release_ack`: `APPROVED arnzqizcycesukplmvuc 5d434a78ac1f997c86b9c92646771de2018cad04`
- `urbanfold.reviewed_baseline_sha256`: the accepted00 baseline digest, never a fixture/staging digest.

Unedited files intentionally STOP. Each file has a single transaction, timeouts, role/staging/metadata guards, fresh-object collision checks and inside-transaction new-table/function security checks. The canonical migration body is copied unchanged between labelled markers; only its outer begin/commit is consolidated into the wrapper. Existing001/002 policies/functions are not replaced. Existing baseline metadata is checked again before commit. Any error rolls back that file; do not execute a selected middle section or COMMIT an aborted partial sequence.

1. Apply10/003 only. Run30: two new survey helpers + survey_notification_events expected, registration objects still absent, existing baseline digest unchanged. Capture the result before proceeding.
2. Re-run00 for collisions/unchanged baseline. Apply20/004 only;003 existence required. Run30 again:14 helpers total (five existing + nine new), all body matches/security metadata correct; all four new tables private/RLS. Inspect exact new policies, constraints, indexes and trigger definitions against source_spec/canonical003/004, not just counts.
3. Effective anon execute false for all14; authenticated execute ONLY get_survey_allowance/get_newsletter_preference/set_newsletter_preference. Service execution required for claim/finish/recovery/payment helpers. Owner postgres and empty search path for all reviewed helpers. Inspect ACLs for unexpected other roles.
4. Authenticated SELECT allowed only on own newsletter_preferences/newsletter_consent_events; no direct customer consent writes or queue access. Service consent audit is SELECT-only. Two enabled Auth AFTER triggers point to record_auth_registration: row INSERT and UPDATE OF email_confirmed_at. No RLS policies on private outboxes is intentional; never add allow-all policies to silence warnings.

003 creates no automatic delivery trigger; it adds bookkeeping/RPCs.004 records future Auth signup/first-confirmation state, queues events, and sends NO network/email itself. Existing accounts are not backfilled and existing consent is not inferred. Already-confirmed newly inserted admin/OAuth users may queue under this implementation; confirm intended production Auth providers/account-creation paths. Unknown existing Auth/DDL trigger side effects must be resolved before installation.

Future live counters can change legitimately as customers sign up; do not require an empty registration queue after enabling triggers. Keep dispatch disabled until an inventory confirms which entries may be sent. Preserve every record; no customer-data or credit-table UPDATE/DELETE is included in the installer bodies.

## 4. Edge Functions / configuration — backend before frontend

Deploy ONLY individually named approved functions; never deploy all functions from config.toml. Use the pinned wrappers + shared modules or equivalent generated single-file Dashboard sources:

| Function | Exact source for Dashboard | Requirements |
|---|---|---|
| request-survey-notification | supabase/dashboard/request-survey-notification.ts |003; own Auth/ownership/revision check; production Zapier path. |
| dispatch-registration-notifications | supabase/dashboard/dispatch-registration-notifications.ts |004; server dispatch-secret auth; production Brevo API transport. |
| create-survey-checkout | Existing supabase/dashboard/create-survey-checkout.ts | Existing002/Stripe; VERIFY ONLY unless a source mismatch separately requires a reviewed update. |
| stripe-survey-webhook | Existing supabase/dashboard/stripe-survey-webhook.ts | Existing002/matching Stripe endpoint secret; VERIFY ONLY, preserve working service. |

Wrappers are under supabase/functions/<name>/index.ts; shared sources billing.mjs, notifications.mjs, registration.mjs. Existing payment source is unchanged from main. All four use `verify_jwt=false` because handlers verify user tokens/dispatch secret/Stripe signature themselves. Never remove those checks or accidentally require a legacy JWT on the Stripe endpoint.

Settings inventory (names only; configure ONLY with separate approval):

- Supabase-injected SUPABASE_URL, SUPABASE_ANON_KEY and SUPABASE_SERVICE_ROLE_KEY must belong to production. Never copy staging/owner-browser values. Service-role/dispatch/provider secrets remain server-only.
- APP_URL = https://urbanfold.github.io/property-survey/ (shared with existing payment functions; changing it affects checkout/cors/return URLs). Never replace with localhost/staging in production.
- NOTIFICATION_TRANSPORT initially disabled; request gateway returns503 without claiming/sending. Later separately approved mode `zapier`; SURVEY_NOTIFICATION_WEBHOOK_URL is the tested production catch URL in server secrets only. Explicit configuration is important: omitted mode defaults to zapier. Keep old browser webhook/service intact during preparation; coordinate retirement only after secure replacement acceptance.
- REGISTRATION_NOTIFICATION_TRANSPORT initially `disabled` (fail-closed default); later approved `brevo`, plus REGISTRATION_DISPATCH_SECRET (secure >=32 characters), BREVO_REGISTRATION_API_KEY and REGISTRATION_EMAIL_FROM (approved authenticated sender address). The Brevo REST API key is NOT the Auth SMTP password. Mailtrap staging credentials are forbidden here.
- Existing SURVEY_PAYMENTS_MODE, STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET must remain unchanged and mode-consistent. Verify values privately by presence/ownership/mode, never paste them in chat. No new Stripe product or price is required; checkout already creates one600p GBP item. The179-pound service is separate.

Brevo SMTP for Supabase Auth is owner-reported working. Review actual production Site URL/allowed confirmation/recovery redirects and templates so they return to the working production app, not localhost; retain email confirmation. Confirm sender/domain authentication, quotas and leaked-password setting/plan decision. SMTP does NOT configure registration REST delivery or survey Zapier actions. No real confirmation/password request is authorised by this review.

Registration worker recipient is fixed to urbanfolduk@gmail.com and includes account email, server registration/verification dates, and original checkbox Yes/No/Not recorded. An unticked/invalid value is no consent; current withdrawn consent, not historical signup choice, governs future marketing. Worker sends no marketing subscription/API contact-list operation.

Survey payload remains client_email/address/surveyor_name/property_id/submission_id. The gateway does not choose the business inbox: inspect Zapier actions privately to ensure the business receives its required notification while preserving intended customer acknowledgements. A successful catch or provider API response does not prove inbox delivery. Existing public hook must eventually be rotated/retired after the replacement is proven; mere relocation into a secret leaves old copies usable. Coordinate old cached clients/any residual Netlify deployment so the working service is not silently cut off.

## 5. Stripe dependency review, no payment changes

Verify active production endpoint points to stripe-survey-webhook, signature secret matches that endpoint and live/test modes agree. Required event types: checkout.session.completed, checkout.session.async_payment_succeeded, charge.refunded, charge.dispute.created. Preserve exactly600p/gbp/product metadata/user matching; webhook idempotently records verified payment, never client redirect. Test-mode credits intentionally do not unlock live entitlements. Refund/dispute handling revokes unused entitlement without deleting paid surveys.

Review existing successful checkout/webhook/ledger evidence first. Only if evidence is missing, prepare a separately approved controlled test with explicit account/payment/record handling; do not generate a payment just to rerun passed local tests. No Stripe account, key, endpoint, settings, credits or179-pound product is modified by this package.

## 6. Automatic registration delivery scheduling — last and separately approved

Without a scheduler/trusted invoker, confirmed accounts queue but no automatic business email occurs. Do not copy staging006 into production. Template50 uses only production URL and distinct production Vault names:

- urbanfold_production_registration_dispatch: exactly the server REGISTRATION_DISPATCH_SECRET.
- urbanfold_production_public_key: approved production publishable/anon key for the gateway.

Check supported Cron/pg_net/Vault versions/permissions and current jobs first; ensure Vault decrypted secrets, cron commands and net request queues are accessible only to trusted server/operator roles; the script installs no extensions or secrets. Prepare Vault entries through protected approved configuration, not SQL literals/chat. Confirm current worker versions/auth, Brevo mode/sender/API key, intended inbox and pending queue before authorising REAL delivery. Template50 requires the standard two approval/digest parameters PLUS `urbanfold.schedule_ack='APPROVED PRODUCTION BREVO DELIVERY AND SCHEDULER'`. It refuses any existing registration-dispatch job instead of duplicating it.

It schedules one server invocation/minute, one pending event/call. Atomic security caps remain5/minute and50/hour independent of scheduling. Stale sending after5 minutes becomes uncertain on later claim/recovery; no automatic replay. Accepted means transport accepted, not guaranteed inbox delivery. Review operator reconciliation rather than resetting states or rerunning claims blindly.

After approved scheduling run51: exactly one expected job, active, correct cadence/production URL/Vault references. Inspect allowed fixed-field worker logs/provider message evidence and queue states without returning tokens, payloads or customer email contents. Future controlled delivery tests use only approved owner-controlled identities/recipients and separately approved production test records, never staging UUIDs/customer submissions.

## 7. Post-install / release evidence and rollback

Backend preparation is NOT permission to merge/publish. Frontend must not switch until003/004/newfunctions/configuration are ready and controlled delivery/authorization is accepted. Preserve current frontend/old webhook during backend setup. New registration triggers can begin queueing before the frontend changes; pause worker/scheduler, NOT consent recording, while delivery is disabled.

Record source hashes, project/operator/approval/time, before/after baseline digest, read-only checks, actual deployed function builds/JWT settings, private provider/scheduler evidence and any separately approved tests. Current Pages workflow publishes main only and explicitly packages root app/index + vendor. Never publish static-client/oldZIP/test fixtures or run production staging-only migrations005–011/setup/seeds/cleanup. Do not deploy staging-notification-receiver or configure staging_capture in production.

Failure handling:

1. Guard/DDL/lock error before commit: that file rolls back. Preserve error/context without secrets and STOP.003 may have committed separately if004 fails; leave its additive empty/private objects and existing services intact. Do not reinstall001/002, drop schema, edit credits, reset users or continue selected statements.
2. Unexpected postcheck/source/ACL difference: do not enable transports/scheduler or release frontend. Inspect exact current metadata; preserve queued/audit/event evidence. Prefer targeted forward correction, not removal of tables or grant weakening.
3. Dispatcher/provider problem: separately approve pausing ONLY its exact production schedule (using inspected job ID in supported dashboard) and REGISTRATION_NOTIFICATION_TRANSPORT=disabled. Preserve queue. Do not reset accepted/uncertain/sending to pending or resend ambiguous events. Restore a verified compatible saved worker only with approval.
4. Signup/confirmation broken by new recording: after error/source review, separately approve40 with the ordinary parameters plus `urbanfold.auth_recording_action='APPROVED DISABLE REGISTRATION RECORDING'`. It verifies two exact triggers/function body and disables ONLY them, preserving all users/history/RLS. No blanket Auth trigger disable. Once corrected, separately approve41 with `APPROVED ENABLE REGISTRATION RECORDING`; inventory accounts created while paused first. Do not infer their original newsletter choice/backfill automatically.
5. Survey notification failure: saved surveys remain saved. Keep notification-unconfirmed state, inspect event/provider evidence, repair secure gateway; never restore browser-webhook fallback or repeatedly submit to force delivery. Original live path remains until separately approved cutover. Do not rotate a working hook prematurely.
6. Client rollback after future release: save verified Pages artifact and approve a secure compatible rollback/forward fix. Blind rollback to old main reintroduces F01/browser-webhook risks. No merge or workflow dispatch is performed here.
7. No newSQL auto-uninstall is proposed: table/function drops could destroy audit/dedup evidence and break active clients. Production data restoration needs separate incident approval, backups and reconciliation. Old keys/hook retirement is separately approved after cutover, never restored to a publicly exposed value.

## Blocking decisions before any execution/release

- Actual00 production output and independent001/002 comparison; final compatibility/dependency/default-grant verdict. No complete claim can be made from RLS/bucket status alone.
- Review automatic-RLS helper/DDL/Auth triggers privately. If rls_auto_enable exists with unnecessary public/client EXECUTE, establish purpose/extension ownership/dependencies and approve a narrow ACL correction separately; do not copy staging's helper fix blindly.
- Leaked-password protection: enable through supported Auth settings after approval if plan supports it, or explicitly record the residual-risk/plan decision. No SQL workaround or forced upgrade.
- Supported production Auth providers/first-confirmation semantics; outstanding genuine cross-user newsletter authorization check.
- Working notification recipients/templates, separate Brevo REST configuration, scheduler/Vault readiness, no accidental historical/real-customer test sends, and operator handling of uncertain delivery.
- Existing Stripe configuration/evidence; exact backup/recovery/cutover approval; production protected-window owner and source hashes.

The immediate safe next step is **review and run only00 via the connected production read-only integration**, then return the metadata/fingerprint for comparison. Keep credentials/raw unknown definitions private. Installation approval remains pending.
