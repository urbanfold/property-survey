# Verified-registration notifications and newsletter consent — development candidate

No cloud migration, function, scheduler, Brevo configuration or email delivery has been performed by this feature preparation. The production notification system/SMTP/Stripe are untouched. These changes require separate reviewed staging installation before any release.

## Findings in existing signup

`handleSignup()` sends newsletter_subscribed, newsletter_consent_at and newsletter_consent_version as Supabase Auth user metadata. The optional checkbox is unchecked in initial HTML and is not required to sign up. Auth metadata is retained in Auth, but users can update their own user_metadata, and the browser supplies its clock/version. It is not an immutable consent ledger. The app previously had no withdrawal UI or canonical preference table. No existing external marketing-list integration or exact production metadata was inspected; production Brevo SMTP verification/recovery success remains owner-reported.

## Candidate schema 004

- newsletter_preferences: user-owned current opt-in, original signup choice, verification/server timestamps and version. Only authenticated own SELECT; no direct client DML.
- newsletter_consent_events: server-only append of signup request, first confirmation and preference changes, including canonical text/version and server time. User can read only own audit entries; cannot insert/update/delete them. Privileged account deletion cascades the rows; audit retention beyond that needs a business/privacy decision.
- registration_notification_events: one private outbox event per newly tracked Auth user, immutable registration email/date/verification/checkbox snapshot and pending/sending/accepted/uncertain state. No client access. Two separate service-only claim/completion RPCs use row locking/SKIP LOCKED and never blindly retry uncertain sends.
- AFTER INSERT and first-confirmation UPDATE triggers on managed auth.users capture strict boolean signup intent and enqueue only on first Auth email confirmation. No network/email is sent inside an Auth transaction. Only metadata captured on account INSERT is trusted as original intent; later metadata edits cannot change history or the canonical preference.
- No existing users are backfilled/notified or opted into marketing. Previously registered users without a canonical record default unsubscribed and can explicitly opt in. Historic metadata must not be promoted into audited consent without separate review. The change clears the signup checkbox after successful account creation so a later signup does not inherit it.
- get_newsletter_preference / set_newsletter_preference(boolean) use auth.uid, require verified Auth for changes, store server timestamps/text, and never accept a caller-supplied user ID/consent time. A first explicit preference by a historic user is audited even if it is an opt-out; identical repeats are idempotent.

## Email/worker behaviour

`dispatch-registration-notifications` is server-only: it requires a dedicated REGISTRATION_DISPATCH_SECRET bearer value, not a browser token. Its database calls use its platform-injected service-role credential internally. A browser cannot choose the recipient or enqueue a notification.

Production-candidate recipient is fixed **urbanfolduk@gmail.com**. The body contains the verified registration email, original server registration date, verification date and newsletter checkbox choice at registration. It is a service/admin message, sent regardless of marketing opt-in; it does not create a marketing subscription. The checkbox is historical: operators/marketing systems must consult the current canonical preference before sending marketing, including after withdrawal.

REGISTRATION_NOTIFICATION_TRANSPORT defaults disabled. Staging is hard-limited to staging_capture in the exact approved project; Brevo delivery is rejected there even if a key is accidentally present. Future production mode brevo requires a separately approved BREVO_REGISTRATION_API_KEY and REGISTRATION_EMAIL_FROM verified sender. Neither existing production SMTP credentials nor provider settings are read/copied/changed. Node tests replace every provider call with a fake fetcher; no actual Brevo endpoint was contacted.

One invocation claims one pending event. Automatic notices therefore also require an approved server scheduler. Optional staging-only SQL template 006 uses reviewed Cron/pg_net/Vault, reads a narrow dispatch secret from Vault at runtime and contains no secret values. It does not install extensions or supply Vault values. Do not claim the feature automatically delivers until worker invocation/scheduling and receipt reconciliation are tested.

Timeouts, provider rejection and completion-write failures are uncertain/sending and not automatically retried; exactly-once email is not guaranteed. Operators need a delivery-history reconciliation process. Triggers add Auth transaction dependencies: a migration/privilege error could block registration/confirmation, so actual staging signup/confirmation must pass before any production approval.

## Withdrawal and marketing boundary

The dashboard Newsletter preferences dialog loads canonical state, supports explicit opt-in/withdrawal and verifies the saved boolean response. Unavailable backend migrations or network errors leave surveys usable and never claim the preference was saved. Logout clears/closes the dialog and stale-account responses are rejected. Choices remain optional and unrelated to survey credits, £179 Essential Feasibility, account verification and service emails.

No newsletter campaign sender/list sync or one-click email unsubscribe endpoint is implemented here. Before any marketing launch, the sender must honour canonical opt-outs and propagate withdrawals to any provider list, with an unsubscribe mechanism in every marketing message. Do not use the historic mutable metadata or registration email report as a current marketing list.

## Rollout/rollback boundary

Review 004, install only in staging after deployment access/project is confirmed, then test fresh dummy registrations, confirmation, withdrawal/history and rejection cases. Never rerun the original staging baseline. F02 staging capture setup is separate (005 and its receiver). Deploy the dispatcher disabled/capture-only; manually invoke it with the narrow dispatch secret for initial tests, then review any scheduler/Vault setup.

If the new Auth triggers cause staging registration/confirmation failures, stop testing and use an approved targeted disable/drop of only urbanfold_auth_signup / urbanfold_auth_first_confirmation. Preserve queue/audit rows and review the failure; do not disable RLS or reset Auth/customer tables. Disabling the dispatcher/scheduler pauses delivery without undoing consent history. A frontend rollback should preserve the secure F01/F02 baseline; do not restore the exposed browser webhook. Production migrations/deployment/email activation are separate approvals.

## Review update — 2026-11-06

F02 SURVEY capture/timeout/duplicate staging verification has passed; this does not establish registration staging readiness. See `audits/2026-11-06/F02_STAGING_VERIFICATION_PASSED.md`. Full candidate review and next-stage approval gates: `audits/2026-11-06/REGISTRATION_NOTIFICATION_REVIEW_PLAN.md`. In particular, per-user uniqueness and one-event-per-call are not numeric dispatcher rate limits; `sending` lacks a claim-age timestamp/operator recovery plan. No registration SQL, worker deployment, scheduler, secret or email was executed during this review. No candidate runtime code was changed.

## Implemented local improvements — development handoff

See `supabase/staging/REGISTRATION_RELEASE_CHECKLIST.md`. Root004 now adds claim timestamps/reasons, atomic 5/minute and 50/hour global dispatch-attempt limits, and service-only stale-sending recovery after five minutes to uncertain (never requeue). New worker completes against its exact claimed_at and reads persisted state; late workers cannot report a recovered event accepted. Safe fixed-field worker diagnostics and explicit unticked-is-not-consent wording added. Original confirmation-state semantics, strict optional consent/withdrawal/history, fixed recipient and all RLS/server boundaries remain.

Fresh staging installer, read-only pre/post checks and guarded Auth-trigger-only pause SQL are prepared. No SQL, function, secret, scheduler or email has been applied by this handoff. New worker requires the matching three-argument finish RPC in reviewed004; install order and disabled-worker gate are mandatory. Auth/admin/OAuth confirmation-state versus real clicked-link limitations and retention/marketing decisions remain documented. Existing F02 staging evidence is preserved separately; registration staging is not marked passed.
