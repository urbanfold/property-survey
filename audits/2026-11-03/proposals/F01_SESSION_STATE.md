# F01 — targeted fix specification (candidate implemented locally; not deployed)

**Goal:** prevent private information from surviving in the UI/in-memory caches or being restored by old requests after logout/account change. Preserve cloud data and the normal same-user draft workflow.

**Prerequisite:** confirm the intended repository and current deployed source. The repository is now confirmed and a local candidate exists; see ../CANDIDATE_CHANGES.md. No deployed app source was changed.

## Concrete change boundary

Target `app.js` state management, `handleLogout`, the Auth callback, `loadDashboard`, `resumeSurvey`, photo display/signing and the completion callbacks of save/upload/notification operations. Change HTML only where a draft-retention explanation/control is approved. No Stripe, credit, schema or photo-storage permission changes are needed for the UI/session fix.

1. Introduce a session generation/identity token. Each private async operation captures user ID and generation; survey-specific work also captures the property ID/state object. Re-check after every relevant await and before rendering, assigning caches, changing active property, writing drafts or showing success.
2. Centralise teardown: invalidate the generation; disconnect Leica; clear private fields, `appState`, review/PDF content, dashboard entries, cached signed links and image elements; clear password values; reset pending state and return to login. Do not overwrite static UI structure or delete database records.
3. Handle `SIGNED_OUT`, successful account switches and recovery exit consistently. Avoid awaiting Auth API calls from inside Supabase's Auth callback; queue required UI work outside the client's lock. Same-user token refresh must not clear an active survey.
4. Discard delayed reads/signing/image callbacks and suppress old-user success/error/draft side effects. Server requests already accepted may complete; a browser cancellation is not a database rollback.
5. Treat draft loading as private data access: validate owner and property before applying any draft. An unscoped legacy `urbanfold_draft` must never be applied to a different user. Migrate valid legacy entries carefully rather than deleting them blindly.
6. Preserve same-user refresh recovery and readback verification. Do not downgrade a successful cloud save, remove existing photos or change any survey-credit entitlement.

## Device-draft decision to approve before claiming full resolution

Both the current DOM leak and plaintext local storage must be accounted for:

- **Shared-device behaviour:** erase private local drafts/caches when signing out. Warn about unsaved local edits before an explicit logout; allow cancellation so the user can save first.
- **Private-device retention:** if offered, require an explicit keep-drafts choice and explain that another person controlling the browser profile can inspect plaintext local storage. User-ID namespacing is an account-separation control, not encryption.
- Define what happens on involuntary session loss, particularly with unsaved edits. Do not silently introduce draft loss as a security “fix”. If recoverable retention across logout is essential with stronger local protection, design authenticated encryption/key handling separately; a key stored beside the ciphertext does not provide the needed protection.

The minimal session/DOM repair can be reviewed separately, but F01 must not be labelled fully resolved while its chosen persistent-cache policy remains undocumented/unapproved.

## Regression cases

Convert audit `BROWSER-01/03/04` to assertions for corrected behaviour, rather than retaining vulnerable-state success criteria:

- Explicit logout: no prior address, notes, photo data, thumbnails, report text or password values remain in the DOM/in-memory private state.
- Signout in another tab: the current tab locks and cannot resume the cached old identity.
- Switch A to B: A's dashboard, drafts, signed URLs and delayed results do not appear under B.
- Delay a read or photo-sign request, then logout/switch. Resolving it cannot open a private view or repopulate a cache.
- Delay an upload/save/notification completion across a session change. No draft is attributed to the new user and no old result restores a success screen.
- Same-user token refresh, device refresh and allowed draft restoration continue working.
- Chosen draft-retention controls behave as disclosed, including offline signout and session expiry.
- Password recovery, admin all-survey access, private photos, PDF/ZIP, BLE entry and all £6 purchase/allowance tests remain unchanged and pass.

## Definition of ready for release

Minimal reviewed diff, failing-before/passing-after regression results, all existing functional suites passing, agreed draft policy, isolated real-Auth two-account checks, rollback review and explicit production approval. This specification now has a locally tested candidate implementation. It is not a deployed fix; its device-draft policy requires approval before release.
