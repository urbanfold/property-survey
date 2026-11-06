# Verified-registration notification review and staged plan

Date 2026-11-06. REVIEW ONLY: no implementation, SQL execution, function deployment, secret change, Auth user creation, notification/email, scheduler, cleanup, commit, push or merge is authorised by this document. Reviewed source: local base ac15c68 plus approved diagnostic receiver changes. F02 survey staging PASS is separately recorded in F02_STAGING_VERIFICATION_PASSED.md. Production remains untouched. Exact production/staging 004 installation metadata has NOT been inspected.

## Intended behaviour

One operational notification to fixed urbanfolduk@gmail.com when a newly tracked account first becomes email-confirmed. Body: registration email, server registration date/time, verification date/time and original signup checkbox Yes/No (Not recorded where appropriate). An unticked/absent/malformed checkbox never grants newsletter consent. Checked-at-signup is historical; current opt-in can later be withdrawn. The admin message must explicitly say it is not a marketing subscription and that marketing must consult current canonical consent. No automatic provider list subscription or campaign send.

Sample content (future actual email, not a staging send):

    A new Urbanfold account has verified its email address.
    Registration email: dummy@example.invalid
    Registered at (UTC): <server Auth created_at>
    Email verified at (UTC): <server Auth email_confirmed_at>
    Newsletter checkbox at registration: No
    This is an operational registration notice. An unticked box is not consent.
    Check current saved newsletter consent before any marketing contact.

Stage captures this message DATA with recipient urbanfolduk@gmail.com but never contacts that inbox or an email provider. No survey/client name/telephone/address/photo/password/token is needed in the registration notification.

## Source review: what is already sound

004 creates newsletter_preferences (canonical current state, original boolean), newsletter_consent_events (server timestamps/wording/version), and private registration_notification_events (one event per user). All enable RLS. Clients only SELECT their own preferences/audit; no direct DML. auth.uid-based preference RPCs accept no caller user ID/timestamp and require a confirmed account to change state. Repeating an unchanged choice is idempotent. Service role has SELECT, not ordinary UPDATE/DELETE grants, on consent audit. Privileged owner/Auth deletion can still cascade/delete rows; this is not tamper-proof audit storage.

Signup HTML is optional, unchecked and not required. JS sends boolean newsletter_subscribed; success resets checkbox. Later mutable Auth metadata cannot rewrite the captured original boolean. Strict non-boolean/missing metadata defaults to no opt-in. Browser timestamp/version fields are not trusted by 004. Current canonical opt-in remains false until confirmation. UI preference RPC supports withdrawal and stale-account protection. Canonical text matches current displayed wording, version 2026-10-23.

Auth AFTER INSERT and first email_confirmed_at transition triggers do database work only, not HTTP. Dates come from Auth/server. Existing users without captured original signup intent are not backfilled/notified. Further email/metadata changes do not enqueue another event. Queue user_id uniqueness prevents duplicate verification notifications. claim uses FOR UPDATE SKIP LOCKED to assign one pending event per worker; finish only transitions sending to accepted/uncertain. Uncertain events are not reclaimed automatically.

Dispatcher requires a separate >=32-character REGISTRATION_DISPATCH_SECRET, not a customer JWT. Recipient is fixed in server code; browser body cannot override it. Database service-role key is platform-injected, never browser-provided. Transport defaults disabled. Staging_capture is restricted to exact hexhtduvqzleoazusskh, with redirects refused; Brevo mode is rejected in staging even if a key exists. 005 receiver requires actual dummy Auth email and registration email ending @example.invalid; its registration path creates no survey rows/credits. Current diagnostic receiver requires explicit mode and has been tested in survey capture; registration path needs its own cloud tests.

Existing local tests (not new cloud proof): registration SQL isolated PostgreSQL, eight worker/capture handler tests (combined with diagnostics 29 passed), optional preference UI, forged timestamp/version/choice checks, RLS, concurrency, no-retry uncertainty and dummy receiver guards. Tests remain incomplete for the gaps below. No local tests rerun in this review-only turn.

## Findings and targeted recommendations

R01 — CONFIRMED: no numeric global dispatch rate limit. One event per user and one claim per invocation are duplicate/throughput controls, not a burst cap. 006 once-per-minute cron does not prevent concurrent/manual authorised calls or floods of distinct verified accounts. Recommend atomic DB claim limits across all workers using a fixed advisory lock and a server-set claim_started_at timestamp (not signup created_at). Deferred pending events stay pending, not silently discarded; include uncertain/sending attempts in limits. Proposed initial caps: 5 new attempts/minute and 50/hour, subject to owner approval and expected volume; no assumption of provider allowance. Return a distinct throttled result, map to 429, preserve server-only permissions and no auto-retry for uncertain delivery. Supabase Auth signup rate/CAPTCHA settings need a separate metadata review; not verified and not a substitute for dispatcher limits.

R02 — CONFIRMED: a crash after claim or failed completion write can leave sending indefinitely, with no claim timestamp to distinguish age. Add claim_started_at and safe event-level diagnostic state/build logs without email/payload/credentials; design an operator reconciliation report. Never turn old sending into pending automatically: receipt/provider evidence may show delivery happened. Any reconciled terminal state/manual resend needs an explicit reviewed, ID-scoped operation with audit, separate approval and duplicate risk assessment. Test crashes before send, after capture, and during finish.

R03 — CONFIRMED operational risk: Auth triggers are in the signup/verification transaction. SQL/privilege/constraint failure can block those flows. Do not hide errors and silently lose consent evidence. Require real managed staging signup + confirmation-state tests and a tested targeted rollback for only the two new triggers before production. No existing Auth trigger replacement/removal or RLS weakening. Root004 has no staging marker guard; provide a guarded staging wrapper after read-only conflict checks instead of running the whole historical setup.

R04 — CONFIRMED semantics needing decision: triggers observe Auth confirmation STATE, not proof a person clicked an email link. Already-confirmed INSERTs (admin/autoconfirm/OAuth) also enqueue. Recommend initial supported journey email/password with confirmation enabled; decide whether those other paths should notify and what they mean for marketing opt-in. Do not claim admin-simulated confirmation proves email delivery. Existing verified accounts are intentionally not backfilled.

R05 — CONFIRMED privacy/retention gap: queue/audit/email snapshots contain personal data, remain in Gmail/provider logs once emailed, and account deletion currently cascades DB history. Define queue/receipt retention, operator inbox access and account-deletion handling before production; audit is access-controlled, not immutable against administrators. Marketing sender/list synchronisation and an email unsubscribe mechanism are NOT implemented. In-app withdrawal alone does not establish marketing-launch readiness.

R06 — CONFIRMED scheduler gap: 006 is an optional template, not installed or managed-extension-tested here. It checks named Vault secrets but duplicate/missing values and actual Cron/pg_net signatures must be reviewed; pg_net stores request metadata including sensitive headers in privileged tables. Review grants/retention. Keep manual dispatch first; schedule only after rate/crash controls and separate approval. Do not copy the production SMTP secret or service key into cron/browser code.

R07 — production provider review outstanding: future Brevo branch creates an idempotencyKey header but no real provider contract, retry window, delivery status or accepted-vs-delivered behaviour has been verified. Do not infer exactly-once email from staging capture counts. Use separate least-privilege production API credentials and verified sender only after approval; existing SMTP verification/recovery setup remains untouched.

R08 — test/preflight gap: migration IF NOT EXISTS is not schema reconciliation. Actual preexisting table shapes, grants, owners, trigger-name conflicts, generated source and scheduler state must be inspected. Existing dummy A/B predate 004 and must remain untouched; use fresh registration accounts for this feature. Consumer must not infer current marketing consent from historical email snapshot or Auth metadata. Add explicit false/missing/invalid/withdrawal/deletion/OAuth decision tests, plus numerical-rate, stale-claim and logs privacy tests.

## Staged implementation and test sequence

0. DOCUMENTATION / PREFLIGHT (this review only, no DB calls): record F02 pass and baseline; inspect local candidate sources. Next approval: provide SELECT-only metadata preflight for 004 tables/functions/triggers/default grants and Auth configuration. Owner runs it in staging; do not rerun baseline/003/005. Confirm 004/dispatcher/scheduler actual presence instead of assuming installation. Require preserved active deployed source and JWT config before any replacement.

1. LOCAL TARGETED WORK (separate approval): agree rate thresholds, confirmation-path semantics and privacy/retention policy; prepare minimal 004 claim timestamp/cap and dispatcher throttling/recovery diagnostics changes, preserving existing consent rules/service-only ACLs. Regenerate only relevant dashboard worker. Prepare guarded staging installer and explicit rollback/check queries. No gateway/F01/F02/Stripe/£6/£179 changes. Tests use network-disabled PostgreSQL/mock HTTP/dummy data. Present complete SQL/code/diffs and test results before installation approval.

2. STAGING DATABASE (separate approval): SELECT-only preflight on hexhtduvqzleoazusskh, then reviewed 004 installer only if compatible. Install no scheduler. Verify new RLS, owner/search_path, function execute grants, trigger definitions, no real recipients/backfill and unchanged survey/credit baseline. Check signup and confirmation still work. Preserve prior metadata/trigger definitions; test rollback in isolated DB first.

3. STAGING WORKER (separate deployment/configuration approval): deploy dispatch-registration-notifications disabled first, retain verify_jwt=false with internal narrow-secret auth. Configure a new staging-only random >=32-character REGISTRATION_DISPATCH_SECRET through secure fields, never chat/code; enable REGISTRATION_NOTIFICATION_TRANSPORT=staging_capture only when ready. Receiver STAGING_RECEIVER_BEHAVIOUR stays explicit accept; no receiver redeploy needed for the accepted registration path. No Brevo key/sender/SMTP/webhook/Stripe settings. A narrow authorised server invoker/test channel must be available securely; A/B public credentials cannot invoke this worker or read private queues. Do not publish dispatch/service keys in local clients or browser tools.

4. DUMMY AUTH/CONSENT TESTS (separate account/test approval): fresh @example.invalid accounts: true, false, missing, string-true/invalid metadata, plus an unconfirmed control. Original A/B and six F02 fixture rows unchanged. Use supported staging Auth flow rather than direct auth.users inserts. Reserved .invalid accounts cannot receive real verification email: an approved dashboard/admin confirmation tests Auth state transitions only. A real link journey requires a separately approved non-customer test inbox and staging mail configuration; no production SMTP reuse.

   Before confirmation: queue empty, current opt-in false, signup intent audited. On first confirmation: one event with server registration/verification dates and correct original Yes/No; false/absent/invalid must stay unsubscribed. Repeat verification, email change, later metadata edits cannot alter history or duplicate event. Verify owner isolation, anonymous denial, no browser queue/receiver/worker access, no forged user/timestamp/consent version. Verify preferences withdrawal/re-opt-in and unchanged repeated updates; historical notification remains historical. Test approved autoconfirm/OAuth policy separately. Auth failure tests must demonstrate targeted rollback without touching existing auth mechanisms.

5. MANUAL CAPTURE / FAILURE TESTS (separate execution approval): authorise exact per-event dispatch calls first, no schedule or automatic replays. Fixed recipient urbanfolduk@gmail.com is captured DATA ONLY. Inspect fields and timestamps from private queue/receipt via metadata-safe owner query; verify no telephone/address/photo/token payload. Calls without narrow secret and with customer JWT must fail. Capture checked/unchecked accounts separately, repeated and concurrent workers cannot double-claim. Numeric cap crossing leaves pending queue intact; test rolling boundaries locally without backdating live rows. Receiver reject and timeout windows require separately approved global staging-mode changes, no overlapping survey tests, and guaranteed accept restoration. Confirm uncertain/sending never auto-retry; simulate interrupted claim/finish locally then a safe cloud subset. Manual reconciliation required for ambiguous sends.

   Count receipt kind='registration_verified' separately. Snapshot F02 survey baseline and ensure survey_notification_events=25 and kind='survey' receipts=24 / attempts=24 / repeats=0 remain unchanged. Registration tests add no property, credit or photo records. Capture receipts' payloads are private even for dummy tests; redact before sharing evidence.

6. SCHEDULER (later separate approval): only after manual tests pass and claim caps/stale-state review is complete, verify Cron/pg_net/Vault metadata/grants, install reviewed 006, populate only narrow staging dispatch/public-key Vault entries, prove one approved schedule, duplicate scheduler prevention, backlog handling and safe pause. No extension install or cron execution today. Native one/minute scheduling alone is not a hard rate limit.

7. PRODUCTION RELEASE (not included): fresh security/config review and rollback export, launch support-path/consent notice and privacy retention decisions, real test inbox/provider tests, operational monitoring and separate approval for each migration/function/scheduler/provider activation and any frontend deployment. Production SMTP/auth email setup, F02 transport, Stripe and Pages stay unchanged. Do not merge draft PR #1 or interpret F02 staging pass as production approval.

## Pause / rollback strategy to prepare and test

Pause the new dispatcher/scheduler before handling a delivery incident; preserve consent/outbox/receipts. If the new Auth triggers block signup/confirmation, after approval disable only urbanfold_auth_signup and urbanfold_auth_first_confirmation (restore previously exported definitions if any) rather than resetting Auth or disabling all triggers. This pause means newly created users may lack captured original choice; mark them unrecorded and never infer historic consent on restart. Retain audit tables/functions/data; do not run destructive baseline rollback or F02 cleanup008. A dispatcher rollback uses a verified pre-change export and never blindly resends uncertain/sending events. No automatic rollback/change executed by this plan.

## Owner decisions / approval gates

- Accept or amend proposed 5/minute and 50/hour dispatch-attempt caps; choose expected notification delay/backlog tolerance.
- Decide treatment of admin/autoconfirm/OAuth confirmations and existing-user notices (recommended: no historical backfill).
- Approve consent wording/version and a documented queue/audit/receipt/inbox retention and withdrawal policy before production marketing.
- Approve local targeted implementation before any candidate source changes; later separately approve exact staging SQL, dummy accounts/confirmation method, secrets, worker deployment, manual calls/fault modes and scheduler.
- No permission or action is needed on production during these stages.
