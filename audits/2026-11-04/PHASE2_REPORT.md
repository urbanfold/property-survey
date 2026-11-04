# Phase 2 — F02 staging preparation and verified-registration candidate

**Date:** 4 November 2026. **Branch:** plan/security-remediation-2026-11-03, existing draft PR #1.
**Source at start:** local f855073; remote development/PR head 1715020; remote main remained 6874d8a. The prior direct-staging report was already one unpushed commit. This phase adds local candidate code/tests/docs; no push, merge, PR-ready action, production change or cloud deployment was performed.

Exact tested runtime/SQL source SHA-256 values are in phase2-evidence/source-manifest.json. Code was tested in the working tree based on f855073 and then recorded in a local phase commit. This report does not claim the new code is running in Supabase or the live app.

## Priority 1 — F02

Reviewed existing 003 migration and request-survey-notification. 003 remains unchanged: confirmed actor, own/admin parent, current submission marker, property/content and property/revision keys, serialised claims, 20/account and 5/property rolling-day limits, uncertain state/no automatic resend and service-only helper/table ACLs.

Prepared a new same-project capture-only transport plus **staging-notification-receiver**. The receiver contains no SMTP/Brevo/Zapier/email-delivery code, requires server authentication and exact staging project identity, and stores only validated dummy payloads through service-only staging_notification_receipts. Survey properties must begin DUMMY and the Auth actor/contact must use @example.invalid. It records attempt counters to detect accidental re-sends, and supports controlled accept/reject/timeout-after-capture test modes. No production hook is required/copied/rotated. The production candidate's default existing Zapier contract stays in place; staging refuses a real-webhook fallback.

Prepared staging migration **005_dummy_notification_receiver.sql**, config and generated Dashboard deployment files. Exact settings, test matrix, recovery/rollback and deployment order are in supabase/staging/F02_PHASE2_PLAN.md.

### What was actually checked in current staging

Using only the existing dummy credentials/public key and fixed staging host, new read-only probes returned:

- request-survey-notification Edge Function: **404**, still unavailable.
- newsletter_preferences / staging_notification_receipts API tables: **404**, new migrations not installed/exposed.
- Dedicated submitted F02 fixture is still needed; the original A property remains unsubmitted.

Earlier direct staging tests verified ordinary-user 403 denial for the installed 003 tables/helpers. Current dummy credentials cannot inspect the full deployed helper definitions or execute privileged migrations. The existing 003 installation/source parity still needs the approved metadata/deployment connection.

**Cloud deployment/testing is blocked by permission, not completed.** Available credentials authenticate A/B; no Supabase deployment/management token/connection exists and no CLI is installed. Ordinary users must not be allowed to deploy or install SQL. We did not relax permissions or use production credentials to get around this. No current deployed gateway, receiver receipts, live rate/duplicate/failure tests or delivery acceptance is claimed.

### Local tests completed

Node tests validate exact staging transport/project/origin guards, no real-email fallback, existing Auth/RLS/recipient checks, fixed receiver destination/server authentication and server-only registration dispatch. Receiver tests cover accept, reject and delayed-after-capture control; database tests validate dummy-only payload enforcement and receipt attempt counters. Existing F02 handler tests and disposable-PostgreSQL claim/confirmation/ownership/dedup/rate-cap/uncertain tests passed. These are mocked-handler and network-disabled local SQL tests, not deployed Edge Function verification.

## Priority 2 — verified registration / consent

### Existing design finding

The signup checkbox was optional and unchecked initially. Its choice, time and version are sent in Auth user_metadata; the user can update metadata and the browser chooses its clock/version. That stores a preference but is **not an immutable/auditable consent history**. No withdrawal form existed. The app source was reviewed; production Auth metadata values and any external marketing-list integration were not read.

### Prepared candidate

- **004_verified_registration_notifications.sql** adds newsletter_preferences, newsletter_consent_events and registration_notification_events, five fixed-search-path helper/trigger functions and two managed-Auth triggers.
- Server captures strict boolean intent on new Auth INSERT, keeps it ineffective until confirmation, records canonical text/version/server times and ignores later metadata rewrites/forged client clocks. Historic users are not backfilled, emailed or opted in. Unknown previous consent is not treated as proven permission.
- First Auth email confirmation queues exactly one private registration notice; normal metadata/email/password updates do not repeat it. Auth triggers perform no network calls. Admin-created/OAuth initially confirmed users count as Auth-confirmed under this candidate; this is not proof of an email-link click and needs a business decision before production.
- Registration outbox snapshots verified registration email, Auth-created date, verification date and original checkbox choice. Later withdrawal changes current consent and appends history; it does not rewrite what the user originally chose.
- Client direct preference/audit DML is revoked; own read is allowed; verified users change only their own choice through a boolean RPC. Audit UPDATE/DELETE is also denied to service_role; triggers/owner still have legitimate DB-administration/deletion powers. Authorised Auth account deletion cascades audit/outbox rows; retention beyond deletion is not decided.
- Dashboard **Newsletter preferences** supports opt-in/withdrawal; loading/error states cannot falsely report saved consent, and logout/stale-account responses cannot restore its state. Signup resets unchecked after successful account creation. Missing new migrations do not block surveys.
- **dispatch-registration-notifications** is server-only behind a new narrow REGISTRATION_DISPATCH_SECRET. Recipient is fixed to **urbanfolduk@gmail.com** and cannot be overridden by a browser. It includes registration email/date and original checkbox Yes/No. Default transport disabled; staging is capture-only. A future separately approved Brevo mode requires a dedicated API credential and verified sender; no provider call was made except mocked tests.
- Worker claims one event per invocation; optional **006_registration_dispatch_schedule.sql** is a reviewed-template starting point for stage-only Cron/pg_net/Vault, not an installed schedule. Automatic delivery is incomplete until invocation/scheduling is configured/tested. No network calls inside Auth transactions.

Withdrawal is implemented in the candidate account preferences; newsletter campaign sending, provider-list sync and an email one-click unsubscribe endpoint are **not** implemented. Any future campaign sender must honour current canonical opt-outs and include an unsubscribe mechanism. Do not use historic metadata or the registration email as a current marketing list.

## Test evidence and limitations

18 validation targets are now passing after targeted reruns: syntax/dashboard parity, existing billing/F02 handlers, 8 new capture/registration handler tests, new consent/queue/sink SQL, new newsletter UI, existing session security/recovery, survey save/failure/photo/export browser suites, allowance, isolated RLS/credits/F02 SQL, product separation and staging-package static checks. SQL uses disposable network-disabled PostgreSQL, no real Auth/service changes. Test evidence is under phase2-evidence/.

The **initial parallel run had 17 pass / 1 Leica timeout** waiting for its chooser. The unchanged simulated Leica suite passed twice serially. Initial failure log is retained; cause is not proven, so do not claim the flake is fixed. No Bluetooth implementation was changed. Related source changes were rechecked after final targeted corrections; the prior real-staging F01/photo/export evidence remains separate and does not prove new registration migration behaviour.

Tests verify optional/unchecked signup, strict booleans, initial unconfirmed no notice/effective consent, forged clock/version rejection, immutable initial choice, unique confirmation event, no historic backfill, opt-in/withdrawal/own-only access, direct-DML/audit forgery denial, concurrent claims, no automatic uncertain retry, dummy-only captures and 600-pence preservation. Managed Supabase Auth-trigger permissions, actual email-link verification, scheduler extension signatures, provider delivery and deployed Edge runtime still need staging checks.

## Preserved business/production boundaries

No change to 002, billing.mjs or existing payment dashboard files; no £6 price/free/paid/refund rule changed. No £179 checkout/entitlement was added. No production Supabase/Brevo/Stripe/Pages/customer record or live webhook was changed. The F01 recovery design remains intact. The downloaded/local existing staging test app and remote draft PR still run their previously published sources until a reviewed update; no source push was made in this phase.

## Needed access, configuration and decisions

1. **Staging deployment permission:** approve an available staging-restricted deployment connection or a project administrator applying reviewed sources. Account-wide management tokens can have wider reach; do not send one in chat or assume dummy passwords grant deployment rights. No broad credential requirement was silently added.
2. **F02 capture configuration:** reviewed existing 003 parity; stage-only 005 plus receiver/gateway deployment; explicit APP_URL, NOTIFICATION_TRANSPORT=staging_capture, STAGING_RECEIVER_BEHAVIOUR=accept. Platform-injected staging server variables stay inside functions. No production catch URL or real inbox needed.
3. **Registration installation/schedule:** separately review/apply 004 in staging, deploy dispatcher disabled/capture-only, securely generate/configure the narrow dispatch secret, decide an invocation schedule and inspect Cron/Vault permissions. Do not test Auth triggers first in production: a trigger/schema/privilege error can block registration/confirmation.
4. **Policies:** confirm admin/OAuth auto-confirmation counting, existing-user no-backfill/re-consent approach, notification/consent/capture retention and uncertain-delivery reconciliation. Newsletter opt-out propagation and email unsubscribe need integration before marketing sends.
5. **Future production email only:** approved verified sender and dedicated Brevo API credential/delivery test, exact production migration/rollback and explicit release approval. Production SMTP is not a staging test credential. No deployment approval is implied by passing these local tests.

Next safe step is obtaining the staging deployment connection/method, verifying its project scope, then completing the F02 capture-only cloud sequence before registration rollout. No more laptop launcher troubleshooting is necessary.
