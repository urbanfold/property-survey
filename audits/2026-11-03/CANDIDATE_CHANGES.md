# F01/F02 local development candidates — prepared for review

**Branch:** `plan/security-remediation-2026-11-03`  
**Baseline application:** `6874d8ab034df341bb6c32f21f1b94f3279f224b`  
**Status:** implemented and tested locally; not pushed, merged or deployed. No live Supabase/Stripe/automation setting or customer record changed.

## Confirmed source and hosting evidence

The owner's screenshot confirms **`urbanfold/property-survey`**, **Public**, main `6874d8a`, matching the attached remote/source. The owner confirms that **https://urbanfold.github.io/property-survey/** opens the app. That Pages-domain URL plus the checked-in Pages deployment workflow supports GitHub Pages hosting, beyond simply storing files in GitHub.

Direct HTTP and GitHub Pages API inspection were blocked in this environment, so the precise deployed artifact/version was not independently inspected. The old Netlify URL's current accessibility/redirect state is unknown. No host or repository visibility change was made.

## Business invariants preserved

- Ordinary users receive their initial survey free and buy additional property surveys for **£6** each. Independent designers/surveyors are intended users, as is Urbanfold.
- The original `001_secure_access.sql`, `002_survey_purchases.sql`, Stripe billing handler and both generated payment-function files are unchanged from the audited baseline.
- Checkout still fixes 600 pence GBP, one-off, and credit issuance/redemption/refunds retain their existing rules. The browser's checkout/allowance UI gets session-bound completion checks, not a new price or product.
- **£179 Essential Feasibility** remains a separate proposed homeowner assessment/report service. No £179 checkout, entitlement or billing migration was introduced.
- Existing survey, photograph and credit data are not migrated, deleted or rewritten by these candidates.

## F01 candidate

### Code changes

`app.js` adds a session generation/context check, central private-state teardown and logout/account-change handling. Dashboard/survey reads, photo signing, uploads/saves, exports and notification/check-out completion paths discard stale private results. A delayed response cannot re-open a survey after logout; photo signing cannot refill the prior cache. Session teardown aborts supported pending database requests, and save helpers carry the original session/property context through subsequent operations. Same-user token refresh does not intentionally wipe an active survey.

Teardown clears prior fields, photos, review/PDF data, passwords, dashboard and signed-link cache, disconnects Leica and invalidates old callbacks. Draft loading checks owner identity; unattributed legacy drafts require a property already authorised by the cloud read. Signup passwords are cleared after successful account creation.

### Behaviour change requiring approval

**The candidate clears local survey drafts on explicit logout, account switch or session loss.** The owner has approved explicit logout clearing with a clear warning and an opportunity to cancel and save first. Involuntary-session behaviour remains a separate release decision. Cloud-saved surveys remain available. Before explicit logout, a warning allows cancellation to save unsaved work first. The Room Details page explains the policy.

This closes the plaintext-device-retention part of F01, but ending a session with unsaved local-only changes can discard those changes. The policy is a review decision, not an unnoticed production change. If retaining drafts across logout is required, revise the policy/design before deployment; owner namespacing alone does not protect plaintext local storage on a shared browser profile.

### Tests

`tests/test_session_security.py` uses the real browser/client with intercepted requests. It checks cancelled logout preserves work, accepted logout clears private state/drafts, SIGNED_OUT invalidates the UI, delayed reads and signed-photo callbacks cannot restore private state, an account switch broadcasts correctly between two browser tabs, and a foreign-owner draft is rejected. Existing refresh/recovery, save/readback, reset-password, export and simulated Leica suites still pass.

No claim is made that all deployed Auth/session settings or real JWT revocation have been tested. Authorised isolated Supabase testing remains necessary.

## F02 candidate

### Code changes

`notifySurveySaved()` now invokes `request-survey-notification` with only the property ID; it no longer contains/calls the catch URL. The new handler verifies a confirmed Auth user, checks the saved property through the caller's RLS, and uses server-derived submission/contact data. The server trigger URL is read from **`SURVEY_NOTIFICATION_WEBHOOK_URL`**, never browser code. Standard Supabase server credentials remain server-side.

Proposed migration **`003_survey_notifications.sql`** adds a private event table and fixed-search-path, service-only claim/completion functions. Unique property/content and property/submission keys with serialised claims prevent concurrent duplicates and unchanged-content resubmissions. Defaults proposed for approval are **20 events per account and 5 per property per rolling 24 hours**. It contains no changes to existing survey/credit table data or the £6 ledger functions.

The response distinguishes accepted delivery from uncertainty. A timeout or receipt-write failure does not cause an automatic resend; a failed notification does not undo or mislabel survey saving. A server-generated 64-character submission identifier preserves the existing payload shape.

### Business/policy boundaries

- A professional may legitimately notify a saved client email different from their login email; this flow is preserved.
- Sender authentication/ownership and saved-record lookup do **not** independently establish that the recipient controls/consents to the saved client email. The candidate uses bounded owner-authorised client notifications; approve that policy or add verified-contact requirements before release.
- No new marketing subscription is created.
- Event state needs an approved retention/reconciliation process. Uncertain events are not blindly retried, and downstream exactly-once email is not guaranteed.

### Unperformed production requirements

No live notification function or event table has been installed. No secret was set/read and no real email was sent. The **old exposed webhook remains unrotated**, including any historical/Netlify client copies. F02 is not remediated in production merely because its replacement exists on this branch.

The backend must be installed/tested before any client cutover. Retire/rotate the old trigger only after a verified replacement and explicit approval; do not reintroduce a public browser fallback. See [supabase/NOTIFICATIONS.md](/workspace/property-survey/supabase/NOTIFICATIONS.md) for the staged setup/rollback considerations.

## Local verification

Thirteen validation targets passed across the development checks:

| Target | Result |
| --- | --- |
| App JavaScript syntax and generated dashboard parity | PASS |
| Existing Stripe handler tests (8) | PASS |
| Notification handler tests (7) | PASS |
| F01 session/privacy regressions, including two tabs and deferred photo signing | PASS |
| Existing survey recovery/failure suite | PASS |
| Existing actual-client browser/signup/login/photo/export/reset suite | PASS |
| Existing allowance/mobile review suite | PASS |
| Existing simulated Leica suite | PASS |
| Existing isolated RLS policy suite | PASS |
| Existing isolated credit/£6 purchase suite | PASS |
| New isolated notification SQL/ACL/concurrency/rate-cap suite | PASS |
| £6 versus £179 product-isolation audit check | PASS |

The target count includes syntax and generation checks. Test logs and command exit codes are under `candidate-evidence/`; tests were repeated selectively after relevant changes. The original baseline audit evidence remains separately under `evidence/`. HTTP routes/fetchers are intercepted; database tests use disposable `--network none` PostgreSQL. No real account, production database, payment or automation receiver was exercised.

The candidate's CI workflow adds these new checks, but it does not deploy Supabase functions/migrations. No workflow was triggered remotely during this work.

## Required approval sequence

1. Review the concrete development diff and the F01 draft/session-loss policy.
2. Review F02 recipients, rolling limits, retention and reconciliation semantics; inspect the actual automation/template behaviour.
3. Exercise the candidates in an authorised isolated Supabase environment with owner/professional A, B and admin, plus a dummy notification receiver.
4. Resolve the exact deployed `get_survey_allowance()` warning using read-only metadata; its existing source definition was not changed.
5. Record the current deployment artifact/version and investigate the old Netlify endpoint before calling a production cutover complete.
6. Approve the exact backend migration/function/secret sequence, client deployment and old-hook retirement. No main-branch merge, push or production operation has been performed or pre-approved by this document.

## PR preparation update

The owner requested a PR without deployment. Explicit logout warning/cancel/save-first preference is approved. See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) and [PULL_REQUEST.md](PULL_REQUEST.md). The checked-in workflow only publishes main, but GitHub API inspection was blocked and residual external deployment integrations could not be checked. No branch push or remote PR was attempted; remote main remains at `6874d8a` on the latest read-only check.
