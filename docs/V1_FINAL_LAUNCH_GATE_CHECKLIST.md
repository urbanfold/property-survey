# Urbanfold Property Survey V1 — launch gate and approval checklist

**Prepared:** 23 November 2026  
**State:** REVIEW ONLY. This file does not authorise any production change.  
**Draft PR:** https://github.com/urbanfold/property-survey/pull/14  
**Release head checked:** `639e66e36b27eee723136e619712a6f820e01542`  
**Live main checked:** `fbc08c116aeaf56824ac7678f95e8625ddfaeccd`

## Confirmed test evidence

- Full verify workflow `45224863610`: **success**, publish job skipped.
- Isolated administrator RLS + rollback workflow `45224863915`: **success**.
- The PR remains **draft**, open and unmerged; live Pages has not been published from this branch.
- A successful isolated database simulation does not establish a completed production migration.

## Gates still needing work

### 1. Customer-facing readiness

- Review the actual V1 user journey with a realistic customer survey and admin download, verifying saved drafts, private photographs, owner/customer isolation, PDF and ZIP.
- Review account-closure request workflow and privacy/retention language; do not silently assume earlier draft PRs have been integrated.
- Review purchase wording for the one free property survey, the **£6 one-time additional survey**, failed or cancelled payments, and refunds. Do not confuse this with the **£129 Essential Feasibility** service.
- Review notifications/consent and verify actual live opt-in and customer receipt behaviour without sending unsolicited messages.

### 2. Read-only production configuration

- Live Stripe account: a restricted live key called **Urbanfold Survey - Live Checkout v2** exists. User inspected permissions and reported **Checkout Sessions Write** and **Charges and Refunds Read**.
- Live Stripe webhook endpoint is present for `stripe-survey-webhook`. Verify event signatures and expected events independently before activation.
- Live Supabase has a secret named `STRIPE_LIVE_SECRET_KEY`, but its **value and match to the Stripe restricted key are unverified**.
- Supabase `SURVEY_PAYMENTS_MODE` was previously reported as `test` from a screenshot/hash comparison; **recheck its effective value before any switch**. Do not disclose secret material.
- Confirm present `APP_URL`, payment event mode, notification enablement and webhook secret configuration without exposing values.
- Confirm the currently deployed `create-survey-checkout` and `stripe-survey-webhook` differ from the release repository as expected; do not replace them wholesale without a specific versioned migration plan. Existing deployed handlers select `STRIPE_LIVE_SECRET_KEY` in live mode.

### 3. Administrator RLS safety

- The live policy snapshot showed broader administrator writes than the proposed least-privilege configuration.
- Review `docs/V1_LIVE_ADMIN_READONLY_RLS_REVIEW.sql` against a **fresh** `pg_policies` snapshot and relevant grants/RPCs/Storage UPDATE/DELETE paths.
- Isolated tests passed, including restoring original policy definitions; separately rehearse rollback against an **exact production schema/policy clone** and test owner A, user B, admin, anonymous plus photo signed URLs.
- Preserve an authenticated change operator, backup/recovery plan and verified rollback procedure; only then request a narrowly scoped **explicit approval to change live RLS**.
- Review Supabase security advisories, including leaked-password protection availability and three authenticated SECURITY DEFINER functions; do not remove necessary RPC grants without checking application dependencies.

### 4. Separate production approvals — none implied by an ordinary "ok"

Use three distinct approval checkpoints:

1. **Database RLS change:** explicitly approve applying the reviewed owner-only write/admin-read-only policies to the live Supabase project after rehearsal. Verify immediately and stop/rollback on regression.
2. **£6 live payments:** explicitly approve changing payment mode/configuration, only after compatible live key, webhook and end-to-end reconciliation are verified; avoid real charges in testing unless the owner expressly approves a small controlled live transaction.
3. **Website release:** explicitly approve merging the reviewed draft PR to `main`, which triggers GitHub Pages publishing. Confirm live environment bindings and smoke test afterwards.

Any approval should identify the exact operation, project/repository, and version. Never combine unrelated approvals.

## Launch stop conditions

Do not change live data or publish if: tests fail; secrets are mismatched or unknown; stale or extra RLS policies appear; customer ownership or private photo isolation regresses; customer-facing terms are incomplete; admin cannot export; rollback is not verified; or owner has not expressly approved the specific production action.

## Current outcome

**Ready for owner review, not yet ready for unconditional live deployment.**
