# Urbanfold Property Survey — security and stability audit

**Date:** 3 November 2026 (UK)  
**Audit branch:** `audit/security-2026-11-03`  
**Reviewed source:** commit `6874d8ab034df341bb6c32f21f1b94f3279f224b`  
**Status:** source review and isolated tests completed for the attached checkout; requested private-repository identity and live deployment remain unverified.

## 1. Scope, authorisation and important limitations

The user requested the private repository named **`urbanfold-property-survey`**. The only attached checkout is `/workspace/property-survey`, whose configured origin is **`urbanfold/property-survey`**. A read-only `git ls-remote origin HEAD` returned the same commit as the checkout. These names are not assumed to identify the same private repository. Confirmation was requested; until received, this report covers **only the attached checkout**, not an unseen private copy or its £179 implementation.

The original checkout was on branch `work`. A new local audit branch was created before writing audit files. No application code, existing migrations, CI workflow or existing tests were changed. No repository push, deployment, payment, email delivery, production login, live storage upload or live database operation was performed. All new files are under this audit directory.

Browser requests were intercepted by local fixtures. PostgreSQL tests used temporary, digest-pinned PostgreSQL 17 containers with `--network none`; these containers were removed afterwards. SQL permission tests set simulated JWT claims inside that isolated database. They **do not prove real Supabase JWT validation, Auth configuration or deployed Storage API behaviour**.

The exact Supabase warning text, deployed function definition/owner/ACL, deployed policies, current bucket settings, Netlify deployment/configuration, Stripe account configuration and authorised staging accounts were not available. **Live Supabase security has not been verified.**

## 2. Overall assessment and priorities

The existing code has useful protections: owner/admin RLS, private photo signing, database-enforced credit consumption, signed payment webhooks, verification after saves, and recovery drafts. Existing local suites all pass. Additional audit tests nevertheless reproduced gaps those suites do not cover.

| Priority | ID | Finding | Evidence/status |
| --- | --- | --- | --- |
| High | F01 | Logout/session changes do not clear private browser state; a late read can restore a private view after logout | Reproduced locally |
| High | F02 | Client code exposes an email-automation trigger URL and submits unsigned, browser-controlled notification data | Source confirmed; unsigned request reproduced with interception; downstream production abuse not tested |
| Medium | F03 | Base schema is missing from production migrations and application-table access relies on pre-existing grants | Reproduced in isolated databases |
| Medium | F04 | Photo-reference rows can point at another property's storage object | SQL insert reproduced; direct other-owner object read remained denied |
| Medium | F05 | Admin rights depend on a fixed signed email claim, without an MFA assurance-level condition | Policy behaviour confirmed; actual account protection unknown |
| Medium | F06 | Upload restrictions are client-side; bucket size/type constraints and retention are not versioned | Source/configuration gap; deployed limits unverified |
| Medium | F07 | Multi-request saves have no atomic revision/concurrent-editor protection | Source-confirmed limitation; simultaneous-editor loss not newly exercised |
| Medium | F08 | One switch disables both new checkouts and processing of signed payment/refund webhooks | Source-confirmed operational risk; production consequences not exercised |
| Low/medium | F09 | Checkout attempt IDs have no expiry/recovery for expired Stripe sessions | Source-confirmed lifecycle gap; real expired-session checkout not tested |
| Hardening | F10 | No checked-in CSP; dependency vulnerability/advisory status and hosting headers unverified | Absence in source confirmed; no exploitable XSS/CVE claimed |

There is **no confirmed cross-homeowner database or storage-object read/write bypass in the supplied RLS under the isolated tests**. That finding is narrower than a live security sign-off.

The source `get_survey_allowance()` is hardened in several relevant ways; its `SECURITY DEFINER` attribute alone is not evidence of an exploit. The live warning remains unresolved pending its exact text and metadata. The new £179 business service is not implemented in the reviewed source.

## 3. Detailed findings: cause, targeted fix and verification

### F01 — Private state survives logout and identity changes

**Source:** [logout handler](/workspace/property-survey/app.js:89), [session initialisation](/workspace/property-survey/app.js:227), [survey reopening](/workspace/property-survey/app.js:605), [draft storage/loading](/workspace/property-survey/app.js:655), [Auth event callback](/workspace/property-survey/app.js:1342).

**Cause:** explicit logout clears `currentUser`, `currentPropertyId` and the signed-URL map but leaves survey inputs, photo data in `appState`, existing `<img>` sources, dashboard contents and local drafts. The Auth callback handles password recovery but not `SIGNED_OUT` or account switches. Async survey reads have no identity/session-generation check before rendering their result.

**Confirmed locally:**

- After logout, the user was null while the prior address, draft, photo data and thumbnail source remained accessible in the browser.
- A real client `signOut({scope:'local'})` event ended the fixture auth session but left the application's cached identity and dashboard active.
- A deliberately delayed survey read was resolved after explicit logout; it restored the old address and made the private details view visible again.

**Impact:** shared-device privacy and stale/cross-session display. This is not proof that an unauthorised remote user can bypass database RLS. The last repro controls call ordering programmatically; the loading overlay may limit an equivalent same-tab click sequence.

**Targeted fix:** centralise identity teardown, clear sensitive DOM/in-memory/cache state, reset password fields and BLE targets, process logout/account-change events, and use a session-generation token or cancellation mechanism to discard old async results. Explicitly define draft retention: namespace by owner and require owner checks, with a shared-device/private-session policy. Do not silently remove recovery drafts without accounting for existing functionality. Namespacing alone does not protect plaintext local storage from someone controlling the same browser profile.

**Verification:** two fixture accounts and then authorised staging accounts; logout and cross-tab signout/account switch; stale read/photo signing/save callbacks; password-recovery exit; browser back/reopen; shared-device DOM/local-storage inspection; confirm permitted draft recovery still works. Previously issued photo URLs remain bearer links until expiry even after the local cache is cleared.

### F02 — Exposed, unsigned notification trigger

**Source:** [notification request](/workspace/property-survey/app.js:1239), especially line 1252. The full trigger URL is intentionally omitted from this report.

**Cause:** a capability-style Zapier catch URL is included in downloadable browser JavaScript. The browser supplies recipient email, address, name, property ID and submission hash. The hash is not an authentication signature. No token/proof of a verified submission accompanies the outgoing request.

**Confirmed locally:** while `currentUser` was null, a direct call with synthetic data produced the unsigned outgoing request; the fixture intercepted it. No real Zapier endpoint was contacted and no real email was sent.

**Impact:** the trigger is exposed. Spoofed notifications, email abuse and automation costs depend on downstream validation that was not available for review. The browser's local deduplication is not server-enforced authorisation or replay protection.

**Targeted fix:** use an authenticated server endpoint that checks ownership and a saved submission, creates a durable idempotent notification event and sends to a controlled/verified destination. Keep the catch URL server-side. Rate-limit the operation. Once the replacement is verified, rotate the exposed URL with explicit approval; removing it from current source cannot erase past distributions/history.

**Verification:** anonymous/expired sessions, wrong owner, invented submission, altered recipient, repeated event, concurrent retries and downstream failure. Use a dummy receiver, then approved staging automation. Preserve the current distinction between successful survey storage and notification failure.

### F03 — Incomplete database bootstrap and implicit-grant dependency

**Source:** [migration 001](/workspace/property-survey/supabase/001_secure_access.sql:1), [migration 002](/workspace/property-survey/supabase/002_survey_purchases.sql:1), [fixture grants](/workspace/property-survey/tests/database_fixture.sql:48).

**Cause:** migration 001 assumes the seven original survey tables, Supabase Auth/Storage infrastructure and photo buckets already exist. The original table definitions are only represented by the test fixture. Migration 001 creates RLS policies but does not explicitly grant required application-table privileges. Migration 002 explicitly grants its own ledger tables, not the seven original survey tables. The test fixture grants broad table privileges before applying the migrations, concealing that dependency.

**Confirmed locally:**

- Applying migration 001 to an empty database fails because `public.properties` does not exist.
- With the original tables present but their legacy anonymous/authenticated DML grants removed, reapplying both migrations leaves authenticated `SELECT properties` denied.

**Impact:** inability to reproduce/restore a new installation from production migrations alone; deployment failures in environments where new tables do not inherit old Data API grants. This does **not** mean the platform's grant change removed existing live-table grants.

**Targeted fix:** capture a reviewed production baseline and add explicit least-privilege grants in migrations, without weakening RLS. Private surveys do not require anonymous read grants. Version bucket provisioning/settings or document controlled prerequisites. Never apply the destructive test fixture to production.

**Verification:** bootstrap an isolated Supabase environment, not only vanilla PostgreSQL; apply migrations twice; simulate no implicit grants; test owner/admin/anonymous API access; validate constraints and restore from a known-good backup. Reconcile the baseline with deployed metadata before authorising a production migration.

### F04 — Photo-reference ownership is not bound to object ownership

**Source:** [photo-row policies](/workspace/property-survey/supabase/001_secure_access.sql:44), [storage policies](/workspace/property-survey/supabase/001_secure_access.sql:64), [photo URL validation](/workspace/property-survey/app.js:492).

**Cause:** photo-row RLS checks the owner of `property_id`/`room_id`, but does not validate that `photo_url` points into that property's expected bucket and UUID directory. Client validation restricts allowed storage buckets/origin, not the parent property's directory.

**Confirmed locally:** homeowner A inserted a photo row belonging to A that referenced B's known fixture object path. A still could not select B's storage object. Thus **a forged reference was accepted, not an object-read bypass**.

**Impact:** broken-photo/metadata integrity problems. An administrator can sign both owners' objects, so malicious references may contaminate a report/export the administrator later shares. This latter downstream disclosure scenario was not exercised.

**Targeted fix:** validate new photo references on the server against the parent property and expected bucket. Prefer structured object keys. Preserve valid legacy links via a reviewed compatibility path; do not rewrite/remove old photos automatically.

**Verification:** valid references in all four photo categories, another owner's path, another property of the same owner, missing object, wrong bucket, encoded/traversal-like names and legacy URL formats. Test actual signing/download endpoints in staging, including admin export.

### F05 — Email-based admin policy and absent MFA-level enforcement

**Source:** [property policies](/workspace/property-survey/supabase/001_secure_access.sql:28), related child/storage policies, [admin allowance](/workspace/property-survey/supabase/002_survey_purchases.sql:52).

**Cause:** privileged access is based on one fixed email in a signed JWT. Policies do not require `aal2`. There is no server-managed admin membership table or immutable user-ID mapping in these migrations.

**Confirmed locally:** an authenticated simulated claim carrying the configured admin email and `aal1` selected both fixture owners' properties. This is the intentional policy's behaviour. **It does not demonstrate forged JWTs, self-promotion through user metadata, or compromise of the real admin account.**

**Risk:** privilege is tied to email/account lifecycle and to compromise of a single privileged account. Enabling MFA enrolment without checking its assurance level in applicable access controls does not by itself establish an MFA gate for these queries.

**Targeted fix:** after confirming the real admin user ID and recovery requirements, use a protected server-managed role or explicit immutable UID mapping. Consider an `aal2` requirement for privileged access with a tested recovery path. Preserve the intended admin dashboard and all-survey access.

**Verification:** normal owner, genuine admin, changed/reused email, revoked membership, `aal1` versus `aal2`, forged user metadata, expired/revoked tokens and admin recovery in isolated Supabase Auth. These real-Auth cases were not performed.

### F06 — Server-side upload limits and retention are not established by source

**Source:** [image processing](/workspace/property-survey/app.js:720), [upload](/workspace/property-survey/app.js:1109), [private-bucket check](/workspace/property-survey/supabase/001_secure_access.sql:89).

**Cause:** the UI checks an image MIME prefix and recompresses to JPEG, but direct authenticated API callers can bypass JavaScript. Neither migration sets bucket MIME/size restrictions. Compression caps width, not the longest side or decoded pixel count. No versioned orphan-object retention/cleanup process is provided.

**Risk/status:** live bucket limits are unknown. SQL ownership restrictions passed; no production upload abuse, file-parser exploit or public download bypass was claimed. Photo removal deliberately removes the database reference while retaining bytes, which supports recovery but requires a retention decision.

**Targeted fix:** audit existing object formats first, then set suitable bucket MIME and file-size limits and quotas; validate resource limits before costly client decoding; cap both dimensions. Define retention and reviewed orphan cleanup without deleting active/recoverable objects.

**Verification:** authorised JPEG/PNG-to-JPEG flow, malformed/oversized/portrait images, direct non-image uploads, foreign-owner folders, attempted overwrite/delete, signed-link expiry and recovery of retained objects. Real Storage API enforcement remains to be tested in staging.

### F07 — Saves are verified but not transactional or version-locked

**Source:** [multi-request save](/workspace/property-survey/app.js:1124), [readback verification](/workspace/property-survey/app.js:1184).

**Cause:** writes to properties, extensions, rooms and photos are separate requests. A local snapshot fingerprint helps choose between cloud data and device drafts, but it is not an atomic database revision condition. Read-then-insert/update logic can race with another editor.

**Risk/status:** existing injected failure/retry tests pass and retain drafts. Mixed partial writes or concurrent overwrites remain possible; an actual two-editor loss scenario was not newly run in this audit.

**Targeted fix:** initially communicate one editor per survey. Design a small server-side revision check/transaction for related metadata, retaining resumable uploads and compatibility with existing rows. Review existing duplicates before adding uniqueness constraints.

**Verification:** two sessions editing the same base revision, an editor changing during uploads, network failure between writes, conflicting deletes, and stale retries. A losing editor must retain its draft and receive a conflict message rather than overwrite newer work.

### F08 — Disabling checkout also stops webhook accounting

**Source:** [payment configuration](/workspace/property-survey/supabase/functions/_shared/billing.mjs:8), [webhook gate](/workspace/property-survey/supabase/functions/_shared/billing.mjs:95).

**Cause:** `SURVEY_PAYMENTS_MODE` controls both new checkout creation and webhook processing. `disabled` makes the webhook return 503, even for correctly signed pending payments/refunds. The billing document acknowledges the need to replay events.

**Risk/status:** while disabled or otherwise unavailable, legitimate credit delivery/refund revocation is delayed. Unused refunded credits may remain spendable until revocation is processed. No production payment/refund was issued in this audit.

**Targeted fix:** separate the switch that permits new sales from the ability to process signed events in the correct test/live mode. Keep signature checks, exact product/amount checks, service-role-only ledger writes and idempotency intact. Provide reconciliation/replay instructions.

**Verification:** disable new sales after creating a checkout; deliver its valid completion, refund and dispute events; verify credit accounting still completes once and no new checkout can open. Test configuration/key rotation and temporary database failures.

### F09 — Expired checkout lifecycle needs recovery

**Source:** [attempt storage](/workspace/property-survey/app.js:377), [idempotency key](/workspace/property-survey/supabase/functions/_shared/billing.mjs:63).

**Cause:** a UUID in session storage is reused until a recognised return URL clears it. There is no attempt timestamp, expiry handling or expired-session replacement path. Leaving/abandoning a checkout outside the explicit cancellation flow can retain the old attempt.

**Risk/status:** a long-lived tab may reuse an expired checkout/session response. Actual expired Stripe sessions were not exercised; ordinary successful, cancelled and repeated-request cases passed.

**Targeted fix:** track the checkout lifecycle server-side or provide a bounded, verified expired-session recovery. Preserve idempotency so a timeout does not create repeat charges.

**Verification:** abandoned tabs, browser back, expired sessions, delayed webhooks, already-paid sessions, repeated clicks, and multiple tabs. Use Stripe sandbox and no real charges without approval.

### F10 — Browser/dependency hardening remains incomplete

**Source:** [HTML](/workspace/property-survey/index.html:1), [vendored dependencies](/workspace/property-survey/vendor/README.md:1).

**Confirmed:** no CSP is declared in the HTML or tracked hosting configuration. Inline event handlers exist. User-supplied address/notes/report text inspected during this review generally uses `textContent` or input values; no exploitable stored-XSS path was confirmed. Actual HTTP headers were not inspected.

Vendored hashes match their documented values: Supabase JS 2.118.0, JSZip 3.10.1 and html2pdf 0.10.1. Integrity/version pinning is useful but does not establish freedom from current advisories. Transitive dependency versions/CVEs were not fully inventoried against an online advisory database.

**Targeted fix:** review a CSP suitable for the actual host, including photography, PDF/ZIP, Bluetooth and auth recovery; plan minimal inline-handler changes if strict enforcement requires them. Inventory bundled dependencies, check advisories and test any proposed upgrade separately.

**Verification:** inert rendering of HTML-like user text, enforcement in browser reporting mode, login/recovery, image compression/signing, PDF/ZIP, Bluetooth and all permitted network destinations. Re-test before deploying header or library changes.

## 4. Authentication, permissions and private photographs

### Positive evidence from available code and tests

- Password sign-in, account creation, phone/newsletter metadata, recovery-link handling, password policy errors and password visibility behaviour pass client tests.
- The app uses the vendored Supabase client for session persistence/refresh. The browser anon JWT is expected to be public; server access must be enforced by RLS.
- RLS on all seven original tables checks property ownership; nested room photos check their room's property.
- In isolated PostgreSQL, anonymous reads and another owner's reads/updates/deletes were denied; cross-owner child insertion and foreign storage insertion were also denied.
- Three storage buckets are required to be private when migration 001 is applied. Extra permissive policies cause that migration to roll back rather than silently leave access open.
- Storage access checks the property UUID at the beginning of the object key. The app creates UUID filenames within that directory.
- The app signs private photo URLs for 3,600 seconds and caches them for 55 minutes; it does not require making buckets public. Known legacy links are converted to signed links.
- Existing owner/admin/private-storage tests and the expanded audit SQL tests pass.

### Boundaries on those findings

The browser fixture is a fake Auth/REST/Storage server, not Supabase. Its successful sign-in is not proof of password hashing, email confirmation, refresh-token rotation or real JWT validation. Its photo responses are not proof that the deployed buckets are private. PostgreSQL tests apply actual source policies but simulate claims, not the Auth gateway. Actual signed-URL bearer access and expiry must be tested against isolated Supabase Storage.

Historical reports from prior manual testing are useful context but were not repeated against real accounts in this audit. Current email-confirmation settings, rate limits, CAPTCHA, admin MFA, allowed redirect URLs and key rotation remain unknown.

## 5. `get_survey_allowance()` SECURITY DEFINER assessment

**Reviewed definition:** [migration 002](/workspace/property-survey/supabase/002_survey_purchases.sql:48).

The available function:

1. Is deliberately `SECURITY DEFINER`, so it can calculate a caller's allowance using protected ledger/revocation information.
2. Uses `SET search_path = ''` and schema-qualified table/auth references; it contains no dynamic SQL.
3. Obtains the user from `auth.uid()`, rejects a missing identity and accepts no caller-supplied user ID.
4. Returns the caller's allowance flags/counts, not another customer's survey rows or photos.
5. Revokes execution from `PUBLIC` and `anon`, then grants it to `authenticated`.

The isolated catalog confirms `security_definer=true`, fixed empty search path, authenticated execution allowed and anonymous execution denied. The owner in that fixture is `postgres`. Client execution of the purchase/revocation helpers and trigger functions was also denied by ACL checks.

**Conclusion:** no exploitable definer/search-path issue was established for this checked-in definition. This is **not** a declaration that the live warning is harmless or that every deployed overload is identical.

Obtain the exact warning text and metadata for all overloads/any same-named view. A mutable-search-path warning would not match this source definition. A security-definer-view warning would require examining a view, not simply removing the function's modifier. Inspect the actual owner/ACL and return fields before choosing a fix. Blindly changing this function to invoker rights can break allowance/refund checks and the working app.

An optional SELECT-only metadata query is provided in `read_only_metadata.sql`. It has been syntax/shape checked against the isolated fixture and **was not run on Supabase**. It returns policy/grant/function/bucket metadata, not customer records or secrets. It is not a migration or remediation script.

## 6. Exposed credentials and dependency provenance

A redacted heuristic scan of tracked source plus **90 text blobs in reachable Git history** found no matches for Stripe secret/signing keys, private-key blocks, GitHub tokens or AWS access IDs. Four binary blobs were skipped. JWT-role scanning found an embedded **anon** key, not an embedded service-role JWT. Environment variable names for server secrets in Edge Functions are not themselves credentials.

The public anon key is required by the browser client and is not treated as a secret leak. Do not rotate it merely because it appears in source; first examine actual key exposure/privileges and use RLS. The notification catch URL is different: it is a trigger capability exposed in client code (F02), and should be treated accordingly.

Pattern scanning is not exhaustive entropy analysis, provider validation or a guarantee that no secret exists. Supabase/Stripe/Netlify settings and GitHub Actions secrets were not inspected. A private GitHub repository does not make the JavaScript sent to website visitors private. No key values are reproduced in this report or test evidence.

## 7. £6 credits versus the proposed £179 Essential Feasibility service

| Aspect | Existing additional-survey credit | Proposed Essential Feasibility service |
| --- | --- | --- |
| Price | £6 = **600 pence**, GBP, one-off | £179 = **17,900 pence**, business proposal supplied in the audit request |
| Purpose | One additional survey after the lifetime free allocation | A separate professional service; deliverables/fulfilment rules need a separate specification |
| Existing implementation | Browser popup, checkout function, signed webhook, ledger and redemption trigger | No implementation found in the reviewed app/SQL/functions at the baseline commit |
| Payment grant | Verified paid event for `urbanfold_additional_survey`, exact 600 GBP | Must not grant/reprice survey credits accidentally |
| Test mode | Recorded test payments do not unlock live credits | Future test/live separation must be designed and tested separately |
| Refunds | Unused credit revoked; existing surveys preserved | Separate cancellation/refund/fulfilment rules needed |

Current controls passed: validated buyer through Supabase Auth, server-fixed amount/currency, ignored browser price/owner/return-URL tampering, signature/time validation, exact paid-product validation, service-only ledger writes, duplicate webhook idempotency, concurrent credit redemption and rollback on failed property insertion. A success query parameter does not grant a credit.

The additional audit payment test specifically sends browser amount 17,900: checkout remains 600. A signed £179 event carrying the existing survey-credit tag is rejected without a credit write. An event carrying a synthetic future feasibility tag is ignored by the current credit handler. That tag is test input, not evidence of an implemented future product.

**Recommendation:** retain the existing £6 contract unless an explicitly approved change retires it. Give the £179 service a separate product/order/payment/fulfilment model and explicit server-side price rules. Do not replace every `600` with `17900`; it would conflate different products and break existing ledger constraints/events. If £179 is sold through a separate website/payment link, audit that integration too; it was not available here.

## 8. Tests executed

All nine existing commands passed on the reviewed source, with Python Playwright 1.62.0, pyee 13.0.1, greenlet 3.5.5, Chromium 154 and Node 24.19.0.

| Command | Outcome and scope |
| --- | --- |
| `node --input-type=module --check < app.js` | PASS — syntax |
| `python scripts/build_dashboard_functions.py --check` | PASS — dashboard copies match shared handlers |
| `node --test tests/test_billing_handlers.mjs` | PASS — 8 handler tests, all HTTP mocked |
| `python tests/test_survey_flow.py` | PASS — recovery, all sections, retry/idempotence and 12 injected failure points |
| `python tests/test_browser_integration.py` | PASS — real browser/client against fixture: signup/login, create/edit/save, photos, readback, submit, PDF/ZIP, reset |
| `python tests/test_client_allowance.py` | PASS — first/free/additional popup, disabled/cancelled/test checkout, forged return rejection and client review |
| `python tests/test_leica_connection.py` | PASS — simulated BLE, captured payloads, validation and precise fixture cloud recovery; no physical laser used |
| `python tests/test_database_policies.py` | PASS — offline PostgreSQL owner/admin/anon/storage policies and repeatable/fail-closed migration |
| `python tests/test_survey_purchases.py` | PASS — offline PostgreSQL £6 ledger/ACL/refunds/concurrency/address locks and preserved records |

Additional audit scripts also completed successfully:

- `reproduce_browser_findings.py`: reproduced four existing browser-state/notification findings; assertions intentionally demonstrate current vulnerable behaviour, not successful remediation.
- `reproduce_database_findings.py`: expanded SQL isolation/ACL tests; reproduced photo-reference, admin-level, grant and bootstrap gaps; validated optional metadata query in the fixture.
- `check_payment_product_isolation.mjs`: demonstrated £179 cannot accidentally mint/reprice £6 credits in current handlers.
- `scan_credentials.py`: redacted source/reachable-history pattern scan described above.

Existing-suite logs and timing/exit-code evidence are under `evidence/`. These scripts are not added to the production CI workflow. After fixes, convert findings into regression assertions for the corrected behaviour rather than keeping vulnerable-state expectations as acceptance criteria.

## 9. Missing evidence, migrations and tests

| Missing item | Why it matters | Recommended verification |
| --- | --- | --- |
| Exact requested private repository | It may contain different code, policies or the £179 flow | Confirm full owner/repository and reviewed commit; repeat relevant audit there |
| Deployed schema/function/policy snapshot | Source SQL may differ from live definitions | Review SELECT-only metadata without changing policies |
| Production baseline/explicit grants | Rebuild/restore must not depend on implicit legacy settings | Fresh isolated Supabase bootstrap plus migration repeatability |
| Versioned bucket limits/provisioning/retention | Privacy, resource control and recoverability | Inventory existing objects before any settings/cleanup change |
| Browser session transition/race regression tests | Existing functional suites missed confirmed stale-state behaviour | Two accounts/tabs, logout and delayed reads; preserve valid drafts |
| Real isolated Supabase account/API tests | Fixtures do not establish live Auth/Storage behaviour | Authorised A/B homeowner, admin and anonymous HTTP tests in staging |
| Recipient validation/server notification idempotency | Existing notification tests check delivery acceptance, not authorisation | Dummy automation receiver plus authorised staging integration |
| Cross-property photo-reference validation tests | Object access can be secure while metadata is misleading | Wrong owner/property/bucket and admin export tests |
| Actual payment deployment evidence | Portable handler tests do not prove deployed secrets/signatures/Stripe state | Sandbox lifecycle, dashboard-copy parity, refund/replay and expired sessions |
| £179 service/order implementation | Business price is not a survey-credit price | Define and independently test product entitlement, fulfilment, totals and refunds |
| Hosting/dependency audit | Active Netlify/GitHub Pages builds, headers and advisories may differ | Review exact deployed artifact/headers and current dependency advisories |

No authorised real Supabase staging accounts/environment were provided. Email delivery, deployed password policies/confirmation, real token refresh/revocation, signed-photo expiry/anonymous download, actual storage size/MIME enforcement, current Stripe mode and account state were **not performed**. No statement in this report substitutes historical manual checks for a current isolated test.

The workflow in this checkout publishes GitHub Pages, while the user mentions previous Netlify hosting. Netlify environment variables, historic deployed bundles and headers are outside this checkout and were not reviewed. Free-project inactivity pausing was previously reported in this conversation; its current configuration/status and uptime controls were not checked. There is no scheduled database health-check workflow in the reviewed source.

## 10. Approval-based remediation sequence

1. Confirm repository identity and obtain the exact warning/deployed metadata before treating this as the audit of the requested private app.
2. Approve a small session-state/async-result fix with failing-before/passing-after regression tests. Preserve the working survey/BLE/draft flows.
3. Approve a server-authorised notification replacement and a separately controlled webhook rotation; no live rotation occurred here.
4. Prepare baseline/grant, photo-reference, admin and storage hardening changes individually in a development branch. Verify each in isolated Supabase and inspect existing records for compatibility.
5. Keep £6 and £179 product changes separate. Verify their server-side amounts, entitlements and refund/fulfilment behaviour independently.
6. Review test evidence and a concrete diff/rollback plan before approving any merge, deployment or production migration.

**No security fixes, migrations, deployments, production tests or production data changes were applied during this audit.**
