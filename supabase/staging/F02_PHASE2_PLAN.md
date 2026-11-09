# Phase 2 staging deployment and verification plan — not executed

Target is exclusively Urbanfold-Survey-Staging (`hexhtduvqzleoazusskh`). Live production (`arnzqizcycesukplmvuc`), its Brevo/Stripe/hooks/Pages and customer data are excluded. Existing draft PR #1 stays a draft; no merge/push/deployment is implied by this plan.

## Confirmed access / blocker

Cloud environment currently supplies only staging public key and A/B dummy passwords. Those succeeded in real Auth/API/Storage tests. They are deliberately insufficient to execute SQL, inspect server secrets or deploy Edge Functions. No authenticated Supabase deployment/management connection or CLI is available. Do not escalate using an exposed key, relax RLS, extract credentials from the live app or copy production service-role/SMTP secrets.

Deployment needs an owner-approved method: a secure staging deployment connection, or a project administrator installing the reviewed SQL/functions. A general Supabase personal management token can inherit access to other projects; do not assume it is staging-scoped or request it in chat. Any such connection requires an explicit scope/risk decision and secure environment configuration. No new broad credential requirement has silently been added.

## Prerequisites and exact sources

Existing 000/001/002/003 were applied by the owner; metadata screenshots and live ordinary-user 403s support protected helpers. Exact deployed 003 definitions cannot be read with current dummy privileges. Review 003_survey_notifications.sql and confirm owner/function ACL/search_path/body parity through approved metadata access before exercising service helpers.

1. Keep 003 unchanged. Its property/content and property/submission uniqueness, actor/property serialization, confirmed ownership, 20/account and 5/property/24h caps remain authoritative.
2. Review/apply **staging/005_dummy_notification_receiver.sql** in the existing staging database only. It requires the staging-baseline table comment, creates service-only staging_notification_receipts and capture helper, and rejects non-dummy users/recipients/properties. No external webhook or email provider exists in this sink.
3. Deploy **staging-notification-receiver** using its index.ts/shared staging_receiver.mjs or generated dashboard single-file source. Do not deploy this function to production.
4. Deploy the reviewed **request-survey-notification** candidate. Its default production Zapier path remains unchanged in behaviour; explicit staging_capture uses only the fixed same-project receiver and service-side authentication. In this staging project it refuses a Zapier/email fallback.
5. Optional next feature: review/apply **004_verified_registration_notifications.sql** (new tables/triggers/RPCs) and deploy **dispatch-registration-notifications**. This is not part of the old setup bundle; do not rerun setup.sql. 005 does not depend on 004, so F02 can be completed first.
6. After manual capture tests, separately approve **006_registration_dispatch_schedule.sql**, Cron/pg_net/Vault setup and narrow dispatcher secret storage. The scheduler template has not been SQL-runtime-tested against real managed extensions and must be reviewed with their deployed signatures.

All entrypoints record verify_jwt=false intentionally, with explicit handler authentication. F02 validates the real bearer user through Auth and caller-token RLS. Sink validates server-only authorisation; registration dispatcher validates its narrow dispatch secret. Do not remove these checks or expose server credentials to the browser.

## Required staging settings — names, no credential values

| Setting | Staging requirement |
| --- | --- |
| SUPABASE_URL | Platform-injected exact staging project URL (no production target). |
| SUPABASE_ANON_KEY | Platform-injected staging public/legacy anon key. |
| SUPABASE_SERVICE_ROLE_KEY | Platform-injected staging server credential; never copy to chat/client. |
| APP_URL | Explicit approved staging client URL. For current laptop-only capture tests http://localhost:8794/ is permitted **only** in capture mode. Future shared/browser/Stripe tests need an approved HTTPS origin. |
| NOTIFICATION_TRANSPORT | staging_capture, mandatory for this project. No SURVEY_NOTIFICATION_WEBHOOK_URL is needed or copied. |
| STAGING_RECEIVER_BEHAVIOUR | accept initially; controlled reject / timeout_after_capture only during serial failure tests. No arbitrary browser override. |
| REGISTRATION_NOTIFICATION_TRANSPORT | disabled until registration tests; then staging_capture only. Never brevo in staging. |
| REGISTRATION_DISPATCH_SECRET | New high-entropy (at least 32 characters), staging-only narrow worker invocation secret, configured securely (not a dummy account password or Supabase service-role key). |
| Scheduler Vault settings | After approval only: urbanfold_staging_registration_dispatch (same narrow secret) and urbanfold_staging_public_key. No secret literals in Cron SQL/logs. |

Do not configure BREVO_REGISTRATION_API_KEY, REGISTRATION_EMAIL_FROM, live webhook/SMTP/Stripe secrets for staging capture. Keep SURVEY_PAYMENTS_MODE disabled if payment functions are later installed; F02 must not change £6 rules. A project-global APP_URL of HTTP localhost is unsuitable for billing's existing HTTPS check; use HTTPS before separate sandbox-payment integration, without modifying billing code.

## Dummy-only verification sequence

Use fresh dedicated dummy registration/notification accounts/properties; leave the original A/B fixtures usable. No real inbox, original live catch URL or actual customer data is allowed. Sink must assert Auth email ends @example.invalid, survey address begins DUMMY and client contact ends @example.invalid. Include the business admin recipient string as captured registration data only; no mail is sent to that inbox during staging tests.

- Prove sink refuses anonymous/user Auth, a different SUPABASE_URL/project and non-dummy payloads; service-only receipt table cannot be read/written by users. Verify raw payload never reaches an email/network provider.
- F02: missing/expired/unconfirmed Auth denied; A→B property denied; unsaved submission denied; forged recipient/actor/revision/extra/oversized fields rejected. A legitimate saved client email may differ from the professional's login.
- Only on dedicated dummy fixtures mark submitted; submission locks the address under existing rules. Do not submit the original A/B or reset address locks/credits to ease testing.
- First submitted content gives one event/one captured receipt; concurrent/cross-device/unchanged resubmits reuse it; changed content makes a distinct event. Capture attempts counters must remain one for gateway retries, not merely one receipt row after duplicate sink calls.
- Test five changed contents in one property/24h then sixth denied. For actor 20 cap, approved service-side fixture creation may seed additional dummy properties under a dedicated actor using the existing maintenance exemption; this must not modify credit functions, insert real purchases or imply a user could create unpaid surveys normally. Existing local SQL tests already exercise both caps; cloud tests remain unperformed.
- Change receiver behaviour serially: reject before capture; timeout after capture; completion DB failure/claim failure via controlled test setup. Verify uncertain/sending state, no automatic resend, saved survey retained and honest UI status. Inspect actual receipts before any approved manual retry/reconciliation; never blindly reset dedup rows.
- Registration: new dummy account unconfirmed has no notification/effective opt-in. First Auth confirmation queues exactly one event with server dates, email and original boolean choice. Further metadata/email/password updates do not resend. Forced client consent timestamp/version is ignored. Existing users are not backfilled/notified.
- Dispatcher: user/no secret denied; server secret captures one message for fixed admin recipient with checkbox Yes/No; no real email. Duplicate/concurrent claims yield no repeated delivery, timeout/rejection stays uncertain. Test Cron only after manual worker checks; user confirmation via admin is a simulation, not proof of an actual email-link journey.
- Preferences: optional/unchecked signup, server-audited intent, opt-in, withdrawal, cross-user isolation, direct-DML/audit forgery denial, metadata changes cannot alter canonical preference. Future marketing must honour current preference; no list/campaign is enabled by these tests.
- Rerun existing F01, survey save/reload/photo/export, £6, private Storage and simulated Leica checks. Real admin/hardware/email-link/Stripe tests remain separately scoped.

## Rollback / approval

Receiver sends no mail, so keep captured dummy receipts for evidence; retention is a decision. Disable a scheduler/dispatcher first if a test misbehaves; preserve queue state. Auth-trigger rollback is targeted and reviewed as described in REGISTRATION_NOTIFICATIONS.md. Never drop/reset the whole schema, disable RLS, rotate the live webhook or restore a public client fallback. No production deployment is authorised.
