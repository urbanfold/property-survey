# F01/F02 deployment checklist — approval required before production

## Current status and scope

Candidates are preserved on `plan/security-remediation-2026-11-03` in `urbanfold/property-survey`. No remote push, PR, merge, deployment, secret rotation, live SQL or customer-data change has been performed by this checklist.

The owner approves the F01 approach of clearing unsaved local drafts on explicit logout with a clear warning and an opportunity to cancel and save first. The current confirmation provides that opportunity; it does not automatically save to the cloud. Cloud-saved surveys and their recovery remain intact. The owner subsequently approved development/testing of current-tab memory recovery for unexpected expiry. Persistent drafts and private DOM are cleared while locked; only the same user after fresh Auth/property-access checks may recover the active-property snapshot. Different-account sign-in or deliberate logout discards it. Closing/refreshing the tab can lose it. Review this tested behaviour before production approval.

The £6 additional-survey credit system, first free survey and original billing implementation remain unchanged. £179 Essential Feasibility is separate and is not introduced by this release. Existing customer notifications must remain functional during cutover.

## 1. Remote safety gate and PR

- [ ] Check GitHub Settings → Pages, Actions workflows and deployment integrations/GitHub Apps, including any residual Netlify connection. Confirm development-branch pushes and PRs cannot publish production or run live Supabase migrations.
- [ ] Compare remote main with audited `6874d8a`; review intervening changes if different.
- [ ] Push **only** `plan/security-remediation-2026-11-03` once the preceding check passes, then open a draft PR against `main` using `PULL_REQUEST.md`.
- [ ] Keep the PR unmerged. The checked-in Pages workflow publishes on a main push (and manual main run), so merging is a production-deployment action requiring separate approval.

Historical access check: read-only GitHub API inspection returned `Forbidden` on 3 November 2026. Git remote inspection succeeded and showed main at `6874d8a`, but cannot reveal external integrations. The branch was initially left unpushed. After the owner checked integrations, it was pushed; API creation of a draft PR failed with `Post "https://api.github.com/graphql": Forbidden`. The owner subsequently created draft PR #1 and confirmed Verify passed and Publish was skipped. The latest tab-memory changes remain local and must not be pushed until results/risks are reported. This is a verification/access limitation, not evidence of an unsafe integration.

## 2. Isolated staging preparation

- [ ] Create/authorise an isolated Supabase project and staging client origin; use dummy records/photos and authorised owner A, professional B and admin test accounts. Never point tests at production.
- [ ] Establish a reviewed baseline schema and migrations matching the deployed app. The test fixture is not a production schema migration. Inventory missing migrations/grants from the audit before importing a baseline.
- [ ] Capture read-only production definitions separately if approved, including the exact `get_survey_allowance()` definition/warning. This release does not change it or claim its live warning is resolved.
- [ ] Review and apply **`supabase/003_survey_notifications.sql`** in staging only. It adds the private notification-event table and service-only claim/completion functions; review the SQL as a whole, including grants, fixed search paths and content fingerprinting.
- [ ] Deploy **`request-survey-notification`** from `supabase/functions/request-survey-notification/index.ts` and its shared module, or the equivalent checked-in generated dashboard file. Verify generated parity with `python scripts/build_dashboard_functions.py --check`.
- [ ] Configure the function with `verify_jwt = false` as recorded in `supabase/config.toml`: the handler itself must verify the bearer token through Supabase Auth. Do not remove that handler check.

### Server environment configuration

| Name | Staging | Approved production cutover |
| --- | --- | --- |
| `SURVEY_NOTIFICATION_WEBHOOK_URL` | Dummy/test Zapier catch receiver | Existing working catch URL initially, configured server-side only; do not rotate/disable it until replacement fully tested and separately approved |
| `APP_URL` | Exact HTTPS staging app URL | `https://urbanfold.github.io/property-survey/` after confirming current deployment |
| `SUPABASE_URL` | Staging project, injected by Supabase | Production project, injected by Supabase |
| `SUPABASE_ANON_KEY` | Staging project, injected by Supabase | Production project, injected by Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | Staging project, injected by Supabase; server only | Production project, injected by Supabase; server only |

Do not overwrite injected credentials with another project's values. No Stripe secret/product/webhook changes are required. Never put a catch URL or service-role key in client code, PR text or logs. The candidate accepts HTTPS Zapier `/hooks/catch/` URLs; use a test Zap/dummy receiver compatible with that validation.

## 3. Test sequence before production approval

- [ ] Run CI/local checks and preserve logs: syntax, dashboard parity, existing billing, notification handler, session privacy, survey recovery, browser flows/photos/exports/reset-password, allowance/mobile review, Leica, isolated RLS, isolated credit and new notification SQL suites.
- [ ] With real staging Auth: signup/confirmation/login/reset; same-user refresh and retryable-refresh failure preservation; same-ID email updates; temporary expiry recovery only after fresh same-user/property verification; denied/racing recovery, storage failure and tab-close warnings; explicit logout cancellation leaves work intact; save then logout clears device/private state; login restores cloud data. Verify expired-session/account-switch behaviour separately.
- [ ] With real staging RLS/Storage: A cannot read/write B's properties, child rows or photographs, list/download/sign another owner's objects, or invoke privileged notification helpers. Verify intended admin access independently.
- [ ] Create/edit/save/reopen every survey section and photos; compare saved cloud values after refresh and a fresh login. Verify Leica entry and PDF/photo exports remain usable.
- [ ] Submit to dummy receiver with saved client email both equal to and different from the professional's email. Verify actual payload/template compatibility and intended recipients. No marketing subscriptions should be added.
- [ ] Reject unauthenticated/unconfirmed/wrong-owner/tampered requests. Test duplicate/concurrent/unchanged submissions, changed submissions, limits, receiver failure/timeouts and receipt-write failure. Verify uncertain deliveries do not silently resend or imply the survey was lost.
- [ ] Review proposed caps (20/account and 5/property per rolling 24 hours), client-recipient authorisation, event retention, and an operator reconciliation process for uncertain events. Recipient control/consent is not proved by ownership of a survey.
- [ ] Exercise the existing £6 purchase tests without changing live Stripe. Any real Stripe testing needs isolated test-mode configuration and approval; verify £179 cannot create a £6 credit.
- [ ] Preserve evidence and obtain approval for the exact production SQL/function/secret/client sequence. Local tests alone do not verify deployed Supabase security.

## 4. Production cutover — not authorised by this document

- [ ] Record current Pages commit/artifact, Supabase definitions, function versions/configuration and protected backup/restore arrangements. Verify recoverability before changing anything.
- [ ] Apply reviewed migration 003 and deploy the new backend function with approved server configuration **before** client deployment. Leave existing client and catch webhook working.
- [ ] Test the new production gateway with explicitly authorised test accounts/records and intended test recipient; avoid customer sends. Recheck access denial cases and delivery receipts.
- [ ] Only after backend acceptance and separate deployment approval: merge/release the client via the existing reviewed Pages workflow; verify the deployed commit, cache behaviour and cloud recovery.
- [ ] Keep the existing catch URL working until the replacement end-to-end path and actual notification actions have passed. Removing the URL from new JavaScript does not invalidate old public copies.
- [ ] Schedule a separate approved retirement/rotation of the exposed catch URL after testing. Update the server secret, preserve/retest existing automation actions, and address cached clients/old Netlify hosting. Until then the original exposed URL remains a residual F02 risk.

## 5. Rollback and reconciliation

- If backend preparation fails before client release: leave the current deployed client/webhook untouched. Diagnose the new backend; do not deploy the new client. Preserve the additive table and event evidence rather than dropping data automatically.
- If the released client/session change regresses: halt further release actions, preserve the deployed commit and evidence, and prepare a reviewed forward fix or a rollback artifact approved by the owner. A straight revert to the old app reintroduces F01 and the public webhook; do not call that a secure rollback.
- If the gateway fails after client release: surveys must continue saving with the notification-unconfirmed message. Repair/redeploy the authenticated handler or an approved compatible secure client/backend artifact; do not add a public webhook fallback. Customer notification interruption requires prompt operator reconciliation.
- For uncertain/sending events, inspect receiver/email delivery records before any authorised resend. Do not reset event states, delete deduplication rows or repeatedly resubmit to force delivery. Exactly-once downstream email is not guaranteed.
- Do not drop migration 003 tables/functions or remove secrets until no approved client uses them and retention/dependency checks pass. Rollback SQL/data restoration needs separate approval; it must not touch the credit ledger or original surveys/photos.
- Never rotate back to a publicly exposed catch URL after retirement. Keep the tested replacement's secret and automation configuration recoverable through approved secret-management procedures.

## Manual configuration / decisions still needed

1. GitHub access and confirmation of external deployment integrations before push/PR creation.
2. An authorised isolated Supabase project, test accounts and test automation receiver; deployed schema/function parity.
3. Production approval of the development-tested tab-memory recovery behaviour, notification recipient rules/caps, retention and reconciliation responsibilities.
4. Review/approval of concrete production migration, function deployment, server secret setup, client release and any rollback.
5. Separate approval and provider-side configuration for later old-webhook retirement/rotation and residual Netlify handling.

Explicit logout warning/cancel/save-first preference is approved. This does not authorise production execution or resolve the outstanding live security checks.
