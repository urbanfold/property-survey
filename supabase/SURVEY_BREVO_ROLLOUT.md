# F02 two-recipient Brevo integration candidate

**Development branch only. No production migration, deployment, secret changes or live emails.**

Requires the reviewed 003 survey notification table/functions in the same project. Migration `007_survey_brevo_deliveries.sql` adds service-only per-recipient delivery state, independent for `admin` and `customer`.

## Intended delivery
- `admin`: `urbanfolduk@gmail.com`, includes the saved property details and client contact.
- `customer`: `properties.client_email`, acknowledgement only. **This field is user-entered, not independently verified; ensure recipient policy, privacy and consent/typos are reviewed before launch.**
- Both messages originate from the verified `survey@urbanfold.uk` sender using server-held `REGISTRATION_EMAIL_FROM` and `BREVO_REGISTRATION_API_KEY`. No provider key in browser or public GitHub.
- Source must first authenticate the surveyor, read the RLS-visible property and claim an unchanged submitted revision via the existing 003 RPC. Never trust browser recipient or owner fields.
- `NOTIFICATION_TRANSPORT=brevo` only on a separately approved production deployment. Existing `zapier` path remains unchanged for rollback until separately retired, and `staging_capture` remains confined to staging. Mode `brevo` is forbidden in the isolated staging project.
- After claim, `prepare_survey_brevo_deliveries()` creates both `sending` ledger entries before sending either email. `finish_survey_brevo_delivery()` records each recipient separately. If any response is ambiguous, the parent is `uncertain`; repeated requests do **not** automatically retry or resend.
- If the function crashes before both send results persist, a `sending` entry may remain indefinitely. Design a manual reconciliation procedure before relying on recovery. Exactly-once guarantees are not possible from HTTP acceptance alone.
- Historical 003 events do not get two new sends automatically. Never reprocess already accepted/uncertain events.
- Validate rollout order: create 003 production-only after guarded preflight/approval, then 007 and deployed gateway, verify with dedicated staging fake provider tests and controlled production inbox test, then set transport to `brevo`; only after tests retire/rotate the formerly public Zapier catch hook.
- Existing registration dispatcher, Brevo verified-registration settings, £6 credits, Auth SMTP and survey data are outside this feature.
