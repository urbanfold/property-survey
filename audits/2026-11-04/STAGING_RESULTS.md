# Direct isolated staging verification — 4 November 2026

**Project tested:** Urbanfold-Survey-Staging, `hexhtduvqzleoazusskh.supabase.co`.
**Development source:** `1715020`, on `plan/security-remediation-2026-11-03` / draft PR #1.
**Actors:** agreed confirmed dummy A and B, authenticated with their own credentials supplied through environment settings. No service-role or management token was used.

The owner published secure test-environment settings. After runtime propagation the assistant verified both staging logins and real HTTPS/API/browser behaviour directly. This is stronger evidence than the earlier fixtures and screenshots, but covers only the scenarios below. It does not verify production security or establish exact production/staging schema parity.

## Passed against actual staging services

| Area | Evidence |
| --- | --- |
| Auth | A and B sign-in HTTP 200 and fresh /auth/v1/user identity/confirmed-email checks. No credentials or tokens logged. |
| Property reads | Unfiltered REST queries returned one own dummy property for each actor. A direct query for the other property returned zero rows in both directions. Anonymous access HTTP 401. |
| Parent/room mutations | A updated own dummy notes; B's attempted update to A returned zero rows and an A readback confirmed no change. A attempted ownership transfer to B was denied HTTP 403. B could not read or update A's seeded room. |
| Free/£6 rules | Each actor sees only its own allocation, zero purchases/paid credits, free allocation consumed, can_create=false, non-admin, price 600 pence GBP. Actual extra-property insert without credit rejected HTTP 400 URBANFOLD_SURVEY_LIMIT; no property was created. |
| Private Storage | In all three buckets A uploaded a tiny synthetic image, downloaded it authenticated, generated a signed URL and saw it in listing. B's authenticated downloads, signing and foreign-prefix uploads were denied; B's listing excluded it. Anonymous public URL requests were denied. Storage returns HTTP 400 for several denied operations; A's successful controls established that the same objects/routes existed. |
| Photo references | A created exterior, extension-location, sketch and room references. B could not read or insert A's exterior/sketch/room references. Temporary references were removed afterwards. Extension-location cross-user denial was not separately exercised in this run. |
| F02/ledger privilege boundaries | Ordinary A receives HTTP 403 for notification-event/revocation tables and direct purchase-recording, notification-claim and completion RPCs. No purchase or notification event was created by the probes. |
| Real browser flow | Headless Chromium used the generated staging copy, real Auth/REST/Storage responses via the environment HTTPS proxy, and local static assets served in-process. A/B read-check buttons passed. Actual image compression/JPEG upload, full cloud save/readback and subsequent reload/reopen preserved the test measurement and photo. |
| F01 | Simulated local SDK session loss captured the just-entered measurement in tab memory, cleared persistent draft/private UI, and required real same-user Auth/property reads before recovery. Real token refresh preserved measurements. Simulated REST disconnection retained the draft. B sign-in discarded A's recovery; explicit logout cleared identity/drafts. |
| Exports | Own-property PDF function produced actual PDF bytes and ZIP function produced ZIP bytes using saved staging data. This was not an admin-role UI test or visual document review. |
| Cleanup | API test notes and inserted references restored/removed. Browser save added temporary room/photo rows; helper restored original seeded property/room/extension/reference state. A subsequent read-check run again found one seeded A room, one property/free allocation per user and zero paid credits. |

Seventeen read-check assertions and sixteen browser assertions passed; detailed redacted records are in staging-evidence/. API/photo operations are summarised from actual tool results, not an invented raw log. Browser routing forwarded real staging requests/responses; it did not substitute fixture backend data. Initial browser automation timed out on a collapsed room input, restored dummy data and exited; correcting automation navigation allowed the full run to pass. No application source change was required.

## Staging changes and retained artifacts

Only the two fictional staging surveys were targeted. No SQL migrations, schema/policy changes, new Auth users, paid credits, submissions, SMTP messages, notification sends, Stripe calls or production requests occurred during these checks. Auth test sessions were created/refreshed/signed out as part of testing.

Three tiny API-uploaded PNGs and one browser-compressed JPEG remain **private dummy Storage bytes**. Their row references were removed during cleanup, matching the app's current retention model; no object DELETE policy or server privilege was added to delete them. Paths are recorded in api-write-photo-summary.json and browser-retained-objects.json. These are synthetic images, not customer photographs. No tokens, headers, passwords or signed URL query strings are in saved evidence.

## Remaining blockers and unverified cases

1. **F02 gateway is not deployed:** a safe GET availability check returned HTTP 404. The database migration exists and caller restrictions passed, but end-to-end notification Auth/deduplication/rate caps/uncertain delivery against a deployed function remain untested. A new dummy-only receiver, staging secrets and approved Edge Function deployment are required. No production webhook was copied, used, rotated or disabled.
2. **No Stripe integration test/credit added:** source/local tests cover paid £6 logic, but this run did not exercise a real sandbox checkout, synthetic live credit redemption, refunds or address locking after submission. Those need separately scoped staging work. £179 remains separate.
3. **No real signup/reset email delivery:** these manually confirmed dummy accounts use .invalid addresses. Production Brevo success remains owner-reported; no production sender settings/credentials were copied.
4. **F01 expiry was simulated locally:** real reauthentication/property checks and real token refresh were exercised. Actual server-timed session expiry/revocation timing, browser/OS eviction, all multi-tab races and same-user email-change flows remain additional staging scenarios. Tab-memory recovery can still be lost on close/reload.
5. **Admin/hardware:** no approved real staging admin identity exists. Own-property export functions passed; admin cross-account workflow remains untested. A real Leica device/camera cannot be operated by this cloud environment; earlier simulated-device regressions are separate evidence.
6. **Known findings remain:** F04 reference-to-object binding, server upload size/MIME limits/retention, transactional/concurrent-save protections and production function-definition/security-warning parity are not resolved by these passing tests.

## Reproduction/security boundaries

Supporting helpers are in staging-check-tools/. They require the three environment requirements already configured: URBANFOLD_STAGING_PUBLIC_KEY and A/B test-password secrets. Do not put values into source, logs or chat. They hardcode the staging host and agreed dummy IDs. The write/photo and browser helpers perform staging mutations/cleanup and must not be treated as read-only or run on production. Run helpers serially; inspect current dummy baseline first. Build the staging copy locally before running browser_checks.py. It uses no Windows launcher and supplies no user-facing loopback preview.

All results/documentation in this update are local. No merge, Pages deployment, production Supabase/Stripe/customer-data change or new GitHub push was performed during this session. This completes the initial direct staging verification phase; it does not approve production release.
