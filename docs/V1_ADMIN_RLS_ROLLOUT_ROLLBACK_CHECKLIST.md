# Urbanfold V1 — production administrator permissions rollout / rollback checklist

**Status: PREPARATION ONLY — DO NOT EXECUTE IN LIVE SUPABASE.**
Prepared 23 November 2026 for `urbanfold/property-survey` draft PR #14.

## Why this is proposed

A read-only review of the live `pg_policies` on 23 Nov 2026 confirmed that the administrator email `urbanfolduk@gmail.com` is allowed by the existing permissive INSERT/UPDATE/ALL policies for seven survey tables and the private-file INSERT policy. The proposed change makes owner writes owner-only while retaining administrator read/export access. Passing an isolated PostgreSQL test does **not** establish that a production rollout is approved or safe without the checks below.

**Reviewed, not applied:** `docs/V1_LIVE_ADMIN_READONLY_RLS_REVIEW.sql`.
**Passing isolated test:** `tests/test_v1_admin_readonly_proposal.py`.
**Live project:** `arnzqizcycesukplmvuc`.
**Current release:** `release/v1-review-2026-11-23` (draft PR #14).

## Release gates before any live execution

1. Obtain **explicit owner approval specifically to apply the live RLS policy migration**; a generic "ok" to continue review is **not** approval.
2. Capture a fresh, timestamped `pg_policies` snapshot including `schemaname, tablename, policyname, cmd, permissive, roles, qual, with_check` for the seven survey tables and `storage.objects`. Compare with the proposal; **STOP** on any extra/missing/redefined policy.
3. Inventory role grants, callable SECURITY DEFINER RPCs, `storage.objects` UPDATE/DELETE policies, and storage service-role paths. Check whether the app's administrator export requires only SELECT and signed URLs.
4. Rehearse **both migration and rollback** on an isolated clone matching current live schema and policies with three identities: property owner A, different customer B, verified administrator; include a signed-out visitor. Do not use real customer data for destructive probes.
5. Check pre- and post-migration behaviour: owner creates/edits/reads own surveys and photo references; B cannot read/write A's content; admin can view/export A and B PDF/ZIP and signed private photos but cannot INSERT, UPDATE or DELETE their records; anonymous access denied; no unintended access to other buckets.
6. Ensure an authorised operator has a working rollback script generated from the fresh pre-change snapshot. Verify rollback in an isolated clone **before** production. Arrange a production change window and keep audit results.
7. Apply migration in **one transaction** only after steps 1–6 are complete. Verify `pg_policies` immediately afterward and run read-only / non-destructive smoke tests using safe dedicated accounts.
8. If any post-change owner/editor/admin read behaviour regresses, **stop rollout** and use the tested rollback. Re-run verification and document the outcome. Never improvise a broad permissive policy to "fix" access.
9. The Stripe payment-mode change and GitHub Pages publication require **separate explicit approvals**, even if this RLS correction passes.

## Read-only preflight SQL (safe to run after a fresh review)

```sql
SELECT schemaname, tablename, policyname, cmd, permissive,
       roles, qual, with_check
FROM pg_policies
WHERE (schemaname = 'public' AND tablename IN
 ('properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos'))
   OR (schemaname = 'storage' AND tablename = 'objects')
ORDER BY schemaname, tablename, policyname;
```

## Rollback preparation: current-policy baseline

For each affected policy, preserve the **exact** original `USING` and `WITH CHECK` definitions captured at the start of the change. A complete rollback should:

- Restore `urbanfold_properties_insert` and `urbanfold_properties_update` to their pre-change conditions.
- Restore each of the six `urbanfold_manage` child-table ALL policies to its pre-change conditions.
- Drop the six new `urbanfold_v1_admin_select` SELECT-only policies.
- Restore `urbanfold_storage_insert` to its pre-change condition; verify `urbanfold_storage_select` remains unchanged.
- Verify restored `pg_policies` records match the snapshot, and confirm owners and admin export work.

**Important:** No preapproved rollback SQL is attached yet. Do **not** execute a guessed rollback against live data; generate the exact SQL from the fresh snapshot and test it first. Because existing admin write access is broader than the intended final design, rollback is a recovery-only action, not the desired final security state.

## Known production advisories to review separately

- Three SECURITY DEFINER functions are callable by authenticated users: `get_survey_allowance`, `get_newsletter_preference`, `set_newsletter_preference`. Their source was inspected and scoped to `auth.uid()`; no source-only review proves they are safe in all circumstances.
- Leaked-password protection is disabled. Decide on an Auth-setting change separately after confirming plan eligibility and impact.
- Several RLS-protected operational tables have no policies; confirm intended service-role-only access rather than assuming they require public policies.

## Status after document preparation

- No live RLS change made.
- No Stripe payment-mode activation or key replacement made.
- No live GitHub Pages publish or PR merge made.
- **Awaiting:** exact migration/rollback rehearsal against a fresh production policy snapshot, then explicit owner approval.
