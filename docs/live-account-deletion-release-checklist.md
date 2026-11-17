# Live account deletion: release blockers and plan (17 Nov 2026)

**Status: design review only. DO NOT ENABLE LIVE DELETION OR MERGE WITHOUT NEW REVIEW.** The existing staging-only deletion handler must never be deployed unchanged to production.

## Confirmed live differences
- Live project: `arnzqizcycesukplmvuc`; staging: `hexhtduvqzleoazusskh`.
- Staging dummy deletion succeeded for six properties, four Storage objects and one Auth account. Staging receipts and Mailtrap test deliveries accepted.
- A real-world client/account in live may have `survey_credit_purchases` rows. The authorised live fixture `tycohdesign1+urbanfoldauto@gmail.com` has one **sandbox** purchase and no live-mode purchase; the staging deletion handler refuses any payment records. Do not silently cascade-delete financial evidence when removing Auth.
- Live `public.users` references `auth.users` with an ordinary foreign key, not ON DELETE CASCADE; it may prevent Auth deletion unless explicitly handled.
- Live `properties`, `rooms`, photo references, free allocations, newsletter preferences/consents and notification events have cascading relationships; removal via Auth delete risks losing audit/consent evidence without a separate retention decision.
- Live Storage buckets: `exterior-photos`, `sketch-photos`, `room-photos` (all private). No `extension-photos` bucket exists in live. Actual Storage object cleanup is necessary, including orphaned files not represented by photo reference rows.
- Live admin must be authenticated and authorised independently of public UI. Never place a service-role key in browser code.
- The Carrd Privacy Policy draft and customer-facing deletion request changes remain unpublished as of this review.

## Required production design before activation
1. **Intake and identity:** record verified request, request timestamp, identity-validation method, scope of deletion and any retention exceptions; never trust an arbitrary claimant's email alone.
2. **Read-only production lookup first:** enumerates Auth profile, `public.users`, all associated property/room/extension records, photo references, actual Storage objects by owner and property prefix, credits/purchases, notifications and consent. Fail closed on unsupported schema or unexpected files. Protect admin account with server-side identity/role and explicit denylist.
3. **Retention partition:** where there is live payment, refund/dispute, fraud or accounting obligation, retain the minimum required legally relevant data outside the account-linked schema before deletion, with restricted access and documented retention period. Treat sandbox payments distinctly; do not inadvertently remove anything needed for reconciliation. Architectural project files are a separate retention class.
4. **Two-stage closure:** prepare a snapshot and require exact account email, independent approval and short expiry; concurrency controls and DB consistency checks; stop on property count/file count changes.
5. **Storage cleanup:** use Supabase Storage API to remove all authorised objects, not `DELETE FROM storage.objects`; include nested paths and pagination and reconcile object count. Handle partial failures with a resumable, admin-reviewed state machine.
6. **Relational deletion:** explicitly handle `public.users` and all non-cascading rows before deleting Auth, and only after financial retention decisions. Avoid assuming multi-system deletion is atomic.
7. **Audits:** minimally retain deletion-request timestamp, verification and decision evidence, completion timestamp, counts and notices; avoid keeping plaintext personal data without need; enforce service-only privileges, reason codes and retention limits.
8. **Notice:** send customer and admin confirmations only after independently verifying deletion; use existing live Brevo transport with idempotency safeguards and suitable error reconciliation. Do not send test email to a dummy non-deliverable address via live service.
9. **Gated tests:** staging with a dummy payment fixture first, plus unauthorized-user and admin self-delete refusal, unexpected Storage files and failed-delivery simulation. Then manually authorised live fixture `tycohdesign1+urbanfoldauto@gmail.com` only, with separate explicit destructive confirmation and pre-deletion audit snapshot.
10. **Publication:** review UK data protection and terms/cancellation wording and Carrd privacy draft; merge audited PRs only after end-to-end verification. `SURVEY_PAYMENTS_MODE` must remain `test` until separate commercial launch approval.

## Current decision
No live database writes, no live deletion endpoint and no changes to payment mode as part of this assessment.
