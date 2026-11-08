# Urbanfold production registration 004 - review pack (8 November 2026)

**Status: DRAFT / NOT APPROVED / NOT EXECUTED.** Production project `arnzqizcycesukplmvuc`. This pack was prepared only on the GitHub development branch. Never run staging SQL in production.

## Source and immutable boundaries
Canonical migration: `supabase/004_verified_registration_notifications.sql` Git blob `8fb8a5ccd40a81e213502f5cd6c0c8f134242f9c`. The installer below embeds that reviewed migration verbatim except the initial `begin;` is replaced with production guard + the same `begin;`; all operational DDL/function/privilege statements and final `commit;` are retained. Validate programmatically before any approval.

## Files
- `01_install_registration_004_production_REVIEW_ONLY.sql`: single-transaction fresh-only installer. Deliberately blocked by NOT_APPROVED session flag.
- `02_verify_registration_004_production_READONLY.sql`: original tested nine checks, read-only; must be independently authorised before live use.
- `03_pause_registration_auth_triggers_PRODUCTION_REVIEW_ONLY.sql`: deliberately blocked emergency pause, affects only the two new Auth triggers, requires separate explicit authorisation. **Not a complete rollback.**

## Observed, not inferred
On 8 November 2026, a narrowly scoped connected production metadata query found zero 004 tables, functions and Auth trigger names. No customer data was queried. Staging 004 had three tables with RLS, seven expected function signatures and two enabled triggers; all seven function-body SHA-256 values matched reviewed source. Staging registration capture recorded one accepted event and one receipt/attempt, zero pending, uncertain or sending; it did **not** send real email. Existing production Brevo API key and sender configuration were saved by the owner through the Dashboard, not retrieved or independently verified. Production provider, dispatcher, Auth settings and external automation have **not** been verified.

## Mandatory before production approval
1. Privately re-confirm project identity `arnzqizcycesukplmvuc`, current SQL role/JWT state, exact fresh-object absence, roles, baseline RLS/ownership and live Auth provider/config/other trigger compatibility. The installer cannot attest its connection from text alone.
2. Confirm a verified production sender, `survey@urbanfold.uk`; fixed recipient `urbanfolduk@gmail.com`; dedicated Brevo API secret and a distinct narrow dispatch secret. Never put secret values in GitHub or chat.
3. Validate the agreed existing-account policy: no historical backfill and no assumed consent from mutable Auth metadata; clarify newsletter/audit retention, account deletion and marketing unsubscribe requirements. Registration notifications are operational, **not** marketing consent.
4. Save actual live Auth trigger/worker metadata and a targeted emergency procedure. The pause script does not restore an arbitrary pre-existing modified environment.
5. Deploy in **strict order after separately named approvals**: approved installer, authorised read-only postflight, worker with transport **disabled**, controlled delivery configuration and one real provider email test, then explicitly approved scheduling. No automatic email is sent by installing 004.
6. On any unexpected privilege/trigger/schema/provider drift: STOP, do not bypass guards, overwrite or rerun blindly. Preserve the working survey, existing sign-in and recovery, credit rules, Stripe and website.
7. Set the guard approval literal **only following independent approval of the exact action**; changing it is a modification of the reviewed source. Never execute this file just because it appears in a GitHub branch.

## Scope limitations
The installer is a prepared candidate, not a production certification. Existing email/password Auth verification may be affected by new database Auth triggers; stage testing and a controlled rollback/pause are prerequisites. Real email accept versus delivery and exactly-once semantics remain unverified. Emergency pause disables registration history collection for new accounts while active.
