# Production registration scheduler — prepared, not activated

**Live project:** `Urbanfold-Survey` (`arnzqizcycesukplmvuc`). **State:** review only. This package does not authorize creating secrets, enabling extensions, scheduling jobs or sending emails. The existing registration function and Auth records remain in place.

## Current confirmed evidence (8 November 2026)
- Verified registration and consent DB migrations have been installed; nine post-install security checks passed and function bodies matched staging.
- Live dispatcher is deployed; a controlled `tycohdesign1@gmail.com` verification yielded one `accepted` Brevo notification received by `urbanfolduk@gmail.com`.
- Owner restored `REGISTRATION_NOTIFICATION_TRANSPORT=disabled` after this test. This is user-reported and secrets' *values* cannot be independently inspected with the current integration.
- Database extensions: `supabase_vault` installed; `pg_cron` and `pg_net` available but not installed (connector list_extensions).
- Staging scheduler template exists at `supabase/staging/006_registration_dispatch_schedule.sql` and is **not** a production installer.

## Proposed setup; each change needs separate approval
1. Read-only check immediately before any changes: confirm `pg_cron`, `pg_net` and `supabase_vault` state, installed job names, and exact production project. No customer contents or secret values required.
2. Approve installation of `pg_cron` and `pg_net` in production, if still absent. Review extension impact and ensure no other jobs are changed.
3. In Supabase Vault, create two **new narrow credentials**: `urbanfold_production_registration_dispatch` (same byte value already in Edge secret `REGISTRATION_DISPATCH_SECRET`) and `urbanfold_production_public_key` (currently enabled production **publishable** project API key). Do not put either value in chat, code, GitHub or SQL logs. **Important**: the owner previously generated the dispatch secret via PowerShell clipboard; if it was lost, rotate the Edge secret and provision Vault with the newly generated value in a tightly controlled step. Never replace unrelated keys.
4. Inspect both Vault *names only*, without selecting `decrypted_secret`. Review all active existing cron jobs; refuse duplicates and surprising jobs. Perform an isolated authorization check with no pending queue and transport still `disabled`.
5. Approve and install `01_schedule_registration_production_REVIEW_ONLY.sql` as a single transaction after its `NOT_APPROVED` acknowledgement is deliberately changed in a reviewed one-time execution. This runs every minute. Scheduling with disabled transport yields harmless 503 responses but creates periodic calls; it is not a substitute for securing the Edge secret.
6. Post-install inspect `cron.job` and `cron.job_run_details` without exposing credentials; check new function logs and queued notification state. Run one approved new-account test before enabling ongoing Brevo delivery. Explicitly approve setting `REGISTRATION_NOTIFICATION_TRANSPORT=brevo` for permanent delivery.
7. If anything fails, separately approve disabling outgoing delivery and/or unscheduling the **single named job**, then inspect provider/queue history before retrying. Never replay `accepted` or `uncertain` items blindly.

## Important behaviour and limitations
- Each dispatch call claims **at most one** pending event and applies 5/minute and 50/hour database-side limits. A one-minute schedule is a throughput choice; verified signups may queue during bursts and remain pending until subsequently claimed.
- Dispatching is asynchronous; Brevo HTTP acceptance is not equivalent to recipient inbox delivery. Provider timeouts and crashed workers may produce `uncertain` events; never auto-retry uncertain sends without reconciliation.
- Registration and confirmation Auth triggers remain active even while delivery is disabled; they enqueue future verified users. No old-account backfill.
- Existing customer surveys, existing Auth SMTP, Stripe and GitHub Pages are outside this change.
- **Never place the server-only `REGISTRATION_DISPATCH_SECRET` into a browser or shared public webhook.** The scheduler must read it from Vault in the database, not source code.

## References
- Supabase official: https://supabase.com/docs/guides/functions/schedule-functions
- Staging reference: `supabase/staging/006_registration_dispatch_schedule.sql`
