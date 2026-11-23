# Urbanfold Property Survey V1 — controlled release preparation

Status: REVIEW ONLY. Do not deploy, merge to main, or enable real payments without the owner's approval.
Baseline: main at fbc08c116aeaf56824ac7678f95e8625ddfaeccd (18 November 2026).
Preparation branch: release/v1-review-2026-11-23.

## Confirmed provenance

The dedicated staging application lives in urbanfold/property-survey-staging (main, 286ec9e22dd41d5c5028f4adf80bab6eb6f864a1). Its app.js and index.html differ materially from the live source. Do NOT copy staging app.js or index.html wholesale: staging-only Supabase bindings, warning banners, authorization assumptions, and dependency layout need to stay isolated.

Staging report changes, newest first:
- 286ec9e22d — footer wordmark colours
- 540e824b7b — actual Urbanfold PNG logo
- 8724758164 — report branding and colour palette
- f99f4a71ea — branded PDF with photographs inside ZIP
- 1720cc63de — PDF export from saved survey
- 8687bbc320 — authorised-admin PDF/ZIP export fix

Session/privacy candidates in live repository are DRAFT PR #8 (focused deliberate logout privacy), PR #9 (unexpected session recovery); broader PR #1 contains 414 changed files and must not be merged wholesale. Confirm that any changes are integrated exactly once without losing session lock/privacy protections.

## Required release procedure

1. Extract and review narrow, production-safe changes for deliberate logout, unexpected session recovery, and PDF/ZIP report exports. Preserve current production Supabase project binding and current public URL.
2. Confirm that staging-only admin review screens, test accounts, test service credentials, dummy email capture functions, and test fixtures are NOT exposed as production functionality.
3. Reconcile report image/logo assets and tests; the staging application contains different file layout and dependencies. Maintain existing photograph access permissions and private storage policies.
4. Review GDPR account-closure request language and customer-facing £6 one-off purchase disclosures before accepting real money.
5. Confirm SURVEY_PAYMENTS_MODE value without posting secrets. Verify live Stripe key selection, webhook signing secret, and webhook endpoint with read-only configuration checks. Current live DB review showed two test purchases and zero live purchases; no actual live payment acceptance test has been completed.
6. Verify notification activation value when possible; Brevo logs showed 9 Nov 2026 business/customer deliveries, but this alone does not prove the present SURVEY_NOTIFICATIONS_LIVE_ENABLED value.
7. Run lint/syntax, security, regression, isolated browser, PDF/ZIP and payment tests on release branch. Compare resulting release diff against main, perform owner acceptance, then seek explicit approval before any deployment or merge.

## Current guardrails

No changes to live Supabase secrets, live database policies, live Stripe mode, main branch, or GitHub Pages deployment are authorized by this preparation document. Existing draft PRs are not automatically approved.
