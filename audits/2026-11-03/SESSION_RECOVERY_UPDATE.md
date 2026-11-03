# F01 tab-memory recovery — local development update

The owner approved these changes for development/testing only. They remain on `plan/security-remediation-2026-11-03`, associated with draft PR #1, but this update has not been pushed. No production action is authorised or performed.

## Implemented behaviour

- Deliberate logout retains the warning and cancel-to-save opportunity, clears private state/drafts/recovery, and broadcasts deliberate cleanup to other current app tabs for that user.
- Unexpected session loss captures the active property's latest measurements and completed photo data synchronously in tab memory, then clears private DOM, signed-link cache, persistent device drafts and active identity. It disconnects Leica and invalidates pending operations.
- Same-user recovery requires fresh `auth.getUser()` verification and a successful caller-token/RLS property read before any private snapshot is displayed. Signed photo links are prepared again. Failure keeps recovery hidden with an explicit retry control.
- A different user ID discards recovery. Session generation checks reject delayed recovery completion after account changes. Same-ID email changes update the authenticated identity without deleting measurements.
- Normal refresh and retryable refresh/network failures preserve the active work. Existing cloud-save failure recovery remains in place; there is no automatic destructive logout on a failed save.
- Status text distinguishes unsaved changes, a device-only draft, and a verified Supabase save. Quota/storage failure is labelled unsaved, not saved. The recovery notice says the work is not saved to Supabase and may be lost on tab close/refresh; a best-effort browser exit prompt supplements it.
- Existing cloud survey recovery, £6 billing/credits and the F02 handler/migration/payload remain unchanged. £179 Essential Feasibility remains separate.

## Regression verification

`tests/test_session_recovery.py` uses the real vendored Auth client and Chromium with all HTTP intercepted. It covers real successful token refresh, retryable 503 refresh failures, failed network saves, storage quota status, same-ID email changes, expiry immediately after input, hidden/no-persistent recovery, exit warning registration, denied property access/retry, recovered photos/measurements and verified save, account switching during a delayed identity check, cross-tab deliberate logout, and new-tab isolation.

**All 14 validation targets passed locally**, including every existing test suite alongside this new suite; command results and logs are recorded in `session-recovery-evidence/`. The original audit and candidate evidence remain separate. No real Supabase user, live RLS/storage setting, payment or notification receiver was exercised. Passing fixture tests is not live security verification.

## Risks and limits before staging/production

1. **Memory lifetime:** closing, refreshing, crashing, browser/OS eviction or device shutdown can lose the snapshot. Browser exit prompts may be suppressed, especially on mobile. This is a recovery opportunity, not guaranteed offline storage.
2. **Scope:** the snapshot preserves the active existing property's current tab state; it is not an archive of every older device draft or an offline new-property workflow. Completed photo data in the snapshot is retained; unfinished photo processing may need to be repeated. Leica must be reconnected after successful recovery.
3. **Revoked access/network outage:** recovery stays hidden until identity and property access can be checked online. A denied or deleted property is never bypassed using the memory snapshot. The user can deliberately discard work by logging out or using a different account.
4. **Browser privacy boundary:** memory is inaccessible through another account's normal application flow; it is not encryption against someone controlling browser developer tools or executing same-origin scripts. Existing storage removal remains best-effort if the browser refuses it.
5. **Concurrent changes/partial writes:** aborting browser requests does not roll back writes already accepted by Supabase. Recovery does not add transactionality or version locking; review recovered work before saving if another tab/device has edited it.
6. **Cross-tab compatibility:** the deliberate-logout broadcast is for this app version on browsers supporting BroadcastChannel. Older clients or sign-out performed outside this UI may appear as unexpected expiry; private content still locks, but in-memory recovery may remain until a verified same-user recovery, different-user sign-in or tab closure. Real multi-tab/mobile staging checks remain required.
7. **Operational release:** no changes to F02 live prerequisites, notification recipient/cap decisions, old-hook rotation gate, Supabase staging requirements or production approval boundaries. Do not merge/deploy as a side effect of this local update.

Next: report local results/risks to the owner before any push. After approval, update the same development branch/PR; do not create a second app, change main or deploy production. Real isolated Supabase Auth/Storage verification remains required before release.
