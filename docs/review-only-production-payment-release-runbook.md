# Production payment recovery — proposed release and rollback runbook

Status: REVIEW ONLY. No deployment authority. Keep Stripe live payments disabled throughout preparation, staging and production verification. PR #18 remains draft until reviewed.

## Release gates
- All required workflows pass on the exact proposed head.
- Check production function definitions, triggers, table/column privileges, RLS, and payment configuration without exposing secrets.
- Capture the currently deployed function source, versions, gateway JWT settings and original SQL definitions/grants; preserve securely and verify restorability. The previous Git main commit is bebfd9617bdf1e5a408480838f49c89343f23365; verify it is still the correct baseline before release.
- Resolve outstanding bounded recovery issues: older revoked entries must not starve eligible unused credits; incomplete checks must not be presented as exhaustive. Verify older tracked and untracked payments, duplicate checkout attempts, refund ordering and pending payment behavior.
- Verify that payment recovery and the checkout tracking/attestation changes work together in a sandbox-only isolated integration environment. The current recovery handler is deliberately live-mode-only; create a separately reviewed staging-specific adapter/test plan rather than enable live payments to test it.
- Approve checkout tracking retention and verify Stripe restricted key read permissions and webhook subscriptions. The proposed recovery limit is ten checks per account per UTC minute, with a maximum of five sessions per check. The account deletion cascade removes that account’s recovery counter and tracking rows. The 30-day automatic recovery search window is separate from tracking retention. Preserve older checkout references until a cleanup policy accounts for delayed payments and manual recovery.
- Test concurrency, refunds pending or arriving immediately around redemption, direct client attempts, rollback and unavailable Stripe behavior. A 60-second attestation is not an atomic guarantee across Stripe and PostgreSQL.
- Obtain explicit approval for each live mutation. Merging frontend changes alone is not sufficient: the new frontend depends on a deployed recovery function.

## Proposed rollout (separate approvals required)
1. Confirm payment mode remains disabled, preserve existing survey access, and capture restore points.
2. Apply separately reviewed additive SQL prerequisites (tracking and attestation column/function). Defer enabling the new redemption requirement until backend/frontend compatibility is confirmed; split the current combined review SQL into independently reviewed migrations.
3. Deploy reviewed checkout, recovery and webhook source with verified authentication/signature behavior and mode disabled. Verify availability and fail-closed behavior without accepting payments.
4. Publish the exact verified frontend revision after backend readiness. Check login, free survey, own existing survey, administrator read-only review, PDF/ZIP and logout. Test the paid-credit flow in isolated sandbox, not by activating live charging.
5. Apply the separately approved redemption enforcement update only after compatibility and rollback checks. Re-run production non-payment smoke checks and verify mode remains disabled.
6. Stop for a distinct live payment activation decision; do not enable payments as part of this runbook.

## Rollback
- Stop release immediately on failed security checks, owner isolation, survey save, export or backend compatibility. Keep payments disabled.
- Restore original trigger/function definitions and grants from the verified captured versions if the new redemption requirement was applied.
- Restore the known working frontend via reviewed revert and verify Pages publication.
- Restore the prior deployed Edge Function sources/configuration if required; do not assume reverting Git restores Supabase.
- Preserve purchase, redemption, revocation and checkout tracking records. Do not drop tables or discard transaction history as a routine rollback.
- Recheck authentication, first free survey, existing records, export, administrator read-only access and disabled payment mode.
- Record exact versions, timestamps, workflow outcomes and any customer impact. Escalate unresolved payment discrepancies for manual reconciliation.

No production SQL, deployments, configuration changes, merges or Stripe activation are authorized by this document.
