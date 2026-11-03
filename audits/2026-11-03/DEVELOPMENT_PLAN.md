# Urbanfold Property Survey — business-confirmed development plan

**Updated:** 3 November 2026.  
**Branch:** `plan/security-remediation-2026-11-03`.  
**Scope:** documentation and targeted remediation specifications only. Application source, existing SQL, live Supabase, Stripe settings and deployed files remain untouched.

## 1. Confirmed business requirements

### Property Survey application: individual users and independent professionals

- Urbanfold's own architectural work and independent designers/surveyors are intended users.
- An ordinary account receives its initial property survey free.
- Each additional property survey costs **£6 GBP**, a one-off payment, not a subscription.
- Retain existing surveys, photographs, purchased credits, unused credits and access rules.
- Preserve the existing privileged Urbanfold admin workflow unless a separately approved security change replaces its implementation without removing its intended permissions.
- Do not alter the £6 price, free allowance, redemption logic or historical ledger records without approval.

The existing ownership boundary is the authenticated account in `properties.user_id`. A professional can own surveys for multiple clients. `client_email` is a client contact field, **not a grant of access**. Do not make a client's matching email automatically confer ownership, or restrict the application to Urbanfold employees. Sharing a survey between separate accounts would require a separately designed permission model; it is not part of F01/F02.

### Essential Feasibility: a separate professional homeowner service

- Proposed introductory price: **£179 GBP**.
- Includes the owner's professional assessment and report preparation.
- It is not a survey credit, an automatic app entitlement or a replacement for the £6 product.
- No implementation was found in the attached source reviewed at `6874d8a`. This does not establish whether another website/private repository implements it.
- A future implementation must use a separate product/order/fulfilment/refund model. Do not change the credit handler's 600-pence checks or credit ledger constraints to 17,900 pence.

## 2. Repository and deployment verification

| Question | Current evidence | Status |
| --- | --- | --- |
| Attached source repository | Configured origin is `https://github.com/urbanfold/property-survey.git`; read-only `git ls-remote origin HEAD` returns `6874d8ab034df341bb6c32f21f1b94f3279f224b` | Remote identity and HEAD verified |
| Is it the intended private repository? | Request originally named `urbanfold-property-survey`; full intended Code-page URL not yet supplied | Awaiting confirmation before application changes |
| Alternate inferred repository | `git ls-remote https://github.com/urbanfold/urbanfold-property-survey.git HEAD` returned Repository not found | Unavailable; could be private/inaccessible or differently named, not proof of nonexistence |
| Public application URL | User confirmed on 3 November that `https://urbanfold.github.io/property-survey/` opens the app | Current availability confirmed by user |
| Hosting provider | The user-confirmed URL is a GitHub Pages domain and the tracked workflow uses `actions/configure-pages`, `upload-pages-artifact` and `deploy-pages` | Evidence supports GitHub Pages, not merely repository storage |
| Direct live response / deployed commit | HTTP requests and authenticated GitHub Pages API attempts were blocked from this execution environment | Not independently measured; footer version or Pages deployment details still needed to bind source to deployed build |
| Repository visibility | Git transport access does not disclose private/public visibility; repository API blocked | Not independently verified |
| Old Netlify URL | Historical URL `https://urbanfold-survey.netlify.app/`; user reports intentional use ended | Current reachability/redirect/disable state unverified; do not assume retired |

**Current live URL on available evidence:** https://urbanfold.github.io/property-survey/ . Availability is user-confirmed; direct HTTP inspection was not possible. The Pages URL and deployment workflow establish stronger hosting evidence than the presence of files in GitHub alone.

**Before applying app changes:** obtain the intended repository's Code-page URL and compare its source to this checkout. Obtain the app footer's version or the latest Pages deployment commit. If they differ, audit the actual source/deployed artifact and rebase the proposals rather than applying them blindly.

No host migration, Netlify deletion, redirect change or deployment is proposed for immediate execution. If the old Netlify app remains accessible, plan its retirement/redirect separately with approval; otherwise it could continue serving an older vulnerable client after a Pages fix.

## 3. Existing £6 Stripe integration — traced from the source

1. The ordinary user's **Start New Survey** checks `get_survey_allowance()`.
2. If the free survey is consumed and no usable live credit exists, the UI offers one additional survey for £6.
3. The browser calls `create-survey-checkout` with an attempt UUID. It does not determine the price or trusted buyer.
4. The Edge Function verifies the bearer session through Supabase Auth and checks allowance using that user's token.
5. Stripe Checkout is created in one-off `payment` mode for **600 pence GBP**, quantity one, product metadata `urbanfold_additional_survey`, and the verified buyer's user ID. A buyer/attempt idempotency key prevents an identical retry creating a new session.
6. Stripe's signed webhook is verified against its raw body and timestamp. The handler checks the paid status, product, amount, currency, buyer reference and matching test/live mode.
7. Only the server's service-role access can call `record_survey_purchase()` to write the ledger. Session ID/payment-intent uniqueness prevents duplicate credits.
8. `enforce_survey_allowance()` serialises account-level property creation: first free allocation, then one eligible unused live credit per new property. A failed property insert rolls back the allocation/redemption.
9. Test purchases can be recorded but cannot unlock live credits. The browser's success URL never grants a credit.
10. Refund/dispute events revoke unused credit through the separate revocation ledger. Existing property records/photos are preserved.

**Files:** `app.js` (allowance, checkout, return handling); `supabase/functions/_shared/billing.mjs` (server checkout/webhook); `supabase/002_survey_purchases.sql` (ledger, ACL and redemption); generated dashboard function copies and `supabase/config.toml`.

**Evidence:** existing Node and isolated PostgreSQL tests passed. Audit tests confirmed a browser-supplied £179 amount cannot reprice the £6 checkout and a £179 event cannot mint a £6 credit. These are local/mock tests. Prior user-reported Stripe sandbox completion/duplicate/cancel checks are historical context, not a fresh audit of today's deployed functions.

**Still to verify with approval in isolated staging:** deployed function/code parity, actual secret configuration and matching Stripe account/mode, endpoint event subscriptions, real Auth verification, delayed webhooks, refund/replay handling and checkout expiry. No live keys/settings were read or changed. Do not infer that live payments are currently enabled from the existence of the code.

## 4. Targeted remediation proposals

### F01 — private-state teardown and session-bound asynchronous work

Prepared specification: [`proposals/F01_SESSION_STATE.md`](proposals/F01_SESSION_STATE.md).

Keep this as a small security change, not a rewrite. Cover explicit logout, external signout, account switches, recovery exit and delayed callbacks. Preserve ordinary survey creation/editing, verified saving, photos, Leica input and same-user draft recovery.

A device-draft retention choice must be explicit. Clearing the UI alone does not protect plaintext drafts in a shared browser, while deleting drafts without warning would undermine recovery. Do not silently apply a destructive retention policy to existing unsaved drafts.

### F02 — authenticated server-side survey notifications

Prepared specification: [`proposals/F02_NOTIFICATIONS.md`](proposals/F02_NOTIFICATIONS.md).

Replace direct browser calls to the catch URL with an authenticated server endpoint, server-derived saved submission data and durable deduplication/rate controls. Keep the external trigger secret server-side and rotate it only after a tested replacement is ready and approval is given.

Professional users may intentionally have a `client_email` different from their own login email. Do not silently reroute every notification to the account owner or remove legitimate client notifications. Document and approve the recipient rules. This fix must not change Stripe product metadata, credit pricing or survey entitlements.

## 5. Acceptance gates and release order

| Gate | Required evidence | Permission boundary |
| --- | --- | --- |
| A — identity | Correct repository URL; current app/Pages URL; source/deployed commit mapping | Read-only verification only |
| B — local F01 | Minimal diff; old leak/race repros fail; new privacy/draft regressions pass; all existing app suites pass | Separate development branch only, after source identity confirmed |
| C — local F02 | Auth/ownership, payload tampering, recipient rules, deduplication, rate limits and failure tests; £6 suites unchanged | Proposed function/SQL only; no live deployment or secret rotation |
| D — isolated Supabase | Authorised two homeowners/professionals plus admin; actual Auth, RLS, Storage and notification dummy receiver | Isolated environment only; any provisioning/costs approved first |
| E — review | Concrete changes, exact SQL, test evidence, deployment order, rollback and notification-retention policy | Explicit approval before live SQL/function/settings/client changes |
| F — controlled release | Deploy backend prerequisite before client integration; verify no duplicate notifications; preserve surveys/credits | Each production action explicitly approved |

Do not make an uncoordinated client-only F02 change: it could break working notifications if the server endpoint is not deployed. Likewise, deploying the server without retiring the exposed old URL does not remove that old trigger's abuse risk.

## 6. Production rollback requirements

- Preserve and identify the current source/deployed build and backend definitions before release.
- F01 is frontend-only, but a rollback must not restore privacy leaks unnoticed; stop rollout if state/draft recovery regresses.
- F02 should be additive initially. Never delete or rewrite surveys, photos or credit purchases to enable it.
- Do not assume a public browser webhook can be restored safely as a rollback once rotated. Prepare an authenticated fallback or a clear “survey saved, notification pending” state.
- Keep staged notification tests isolated from the real inbox/automation. Never trigger real notifications just to prove the endpoint is exposed.
- Do not combine an Essential Feasibility launch/payment change with the security release.

## 7. Next required input

The app URL has been confirmed by the user. The remaining repository input is its **full GitHub Code-page URL**, plus ideally the app footer version or Pages deployment commit. No passwords, API keys or customer records are needed.

The exact Supabase `get_survey_allowance()` warning and read-only deployed metadata are still required to resolve that audit item. Do not remove `SECURITY DEFINER` or alter permissions solely to silence an unspecified warning.
