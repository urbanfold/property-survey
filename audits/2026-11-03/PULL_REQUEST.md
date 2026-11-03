# Prepare session privacy and authenticated survey notifications

Draft PR target: `urbanfold/property-survey`, base `main`, head `plan/security-remediation-2026-11-03`.

Signing out can leave private survey state in the browser, and survey notifications currently use an exposed browser webhook. These candidates clear private session state, reject stale asynchronous results and route notification requests through authenticated server-side ownership checks and durable deduplication.

Explicit logout warns that device drafts will be removed and lets the customer cancel and save first. Unexpected expiry instead locks private content and keeps an active-property snapshot in current-tab memory for same-ID reauthentication and a fresh property-access check. Different users cannot restore it; closing/refreshing the tab can lose it. Same-user refresh and email changes preserve measurements. Cloud survey records and recovery are preserved. The £6 additional-survey system remains unchanged; £179 Essential Feasibility is separate and is not implemented here.

## Validation

Fourteen local validation targets passed, covering existing authentication, survey persistence/recovery, photo uploads/exports, allowance/credits, simulated Leica input, isolated database policies, and new session/notification regressions. Evidence and limitations are in `audits/2026-11-03/CANDIDATE_CHANGES.md`. Real isolated Supabase account/Storage testing and actual automation compatibility remain outstanding; live security is not claimed verified.

## Release constraints

Do not merge or deploy yet. New notification backend prerequisites must precede the client: migration `supabase/003_survey_notifications.sql`, Edge Function `request-survey-notification` and approved server environment configuration. Keep the existing webhook active until its replacement has been fully tested; retirement/rotation needs separate approval. Source removal does not revoke old public copies.

Review development-tested tab-memory recovery limits, recipient rules, proposed caps (20/account, 5/property per rolling day), retention and uncertain-delivery reconciliation before release. A professional's saved client recipient may legitimately differ from their login email; saved data does not prove recipient consent/control.

Full deployment/testing/rollback checklist: `audits/2026-11-03/DEPLOYMENT_CHECKLIST.md`. This PR must not change live Supabase, Stripe or customer records. The Pages workflow's PR path verifies only; merging into main normally triggers production publication and requires explicit approval.
