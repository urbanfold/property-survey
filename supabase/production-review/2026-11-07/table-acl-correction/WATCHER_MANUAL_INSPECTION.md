# PostgREST watchers: limited manual inspection — 7 November 2026

**PARTIAL SUPPORTING EVIDENCE. Full watcher verification remains OPEN; production SQL03 is not approved or executed.** This update changes documentation/evidence only. It does not alter functions, fingerprints, SQL03/05, approval parameters or production permissions.

## What the operator reports

The owner reports opening the existing production functions with the approved read-only definition query in Supabase SQL Editor for project arnzqizcycesukplmvuc:

| Existing function | Manual finding | Previously recorded body fingerprint, reported unchanged |
|---|---|---|
| extensions.pgrst_ddl_watch() | `NOTIFY pgrst, 'reload schema';` on line26 | de987df746eb39647098459e7993bd8595e592969b0cd647828a3d13d37cffe0 |
| extensions.pgrst_drop_watch() | Same statement on line24 | 791b41f0632fc86e0fc86a303ec0fd710c4e2ecf947a23422dae2b7a2c122f1d |

The operator found no occurrences of **http, webhook, email, EXECUTE or PERFORM** in either function. Line numbers are reported observations, not independently reproduced here; definition/body rendering can affect line numbering. Search method/case sensitivity were not specified and are not assumed comprehensive. Complete bodies were not supplied to this development agent.

These findings support the expected PostgREST schema-cache refresh purpose. The displayed NOTIFY sends a database notification to the PostgREST listener; it is not a customer email or an HTTP webhook. Stable hashes tie the reported observations to the previously recorded bodies but are not a trusted-provider identity/behaviour proof.

The earlier evidence that both functions are enabled, supabase_admin-owned, SECURITY INVOKER and fixed-empty-search-path remains recorded. None of these metadata attributes, the one NOTIFY statement or the five negative keyword findings proves that every other branch/query/indirect call is harmless. There is no new evidence of suspicious behaviour or a reason to modify/disable provider watchers.

## What remains before execution approval

**One focused watcher source review is still needed**, not another retrieval/search loop or a full application audit. Have a competent authorised reviewer read the complete **already retrieved** definitions privately, tracing all branches and referenced routines. Record whether their behaviour is limited to the expected event-trigger catalog inspection/filtering and fixed PostgREST cache notification. In particular, establish whether there are any other data/permission changes, dynamic SQL or unreviewed indirect calls that could perform external/process/email/payment actions. Ordinary catalog reads, control flow and fixed NOTIFY are expected; a keyword scan alone cannot answer this.

A comparison with a trusted provider definition appropriate to the deployed version is an alternative/supporting way to establish the standard implementation. Do not require an arbitrary latest online version to match, copy provider code over production, or claim provider provenance was verified when it was not. A complete qualified private body review can establish the behavioural conclusion without pretending an upstream comparison was performed. If either approach leaves behaviour unexplained, keep the gate open and withhold execution approval.

Keep complete definitions in the trusted administrator/private review channel; do not commit raw functions or embedded secrets in the repository. Report only the exact functions/fingerprints, review method, trusted version/reference if one was used, the non-secret conclusion and any limitations. Do not invoke the watchers, change their owner/security mode, disable them or send a notification as a test. The read-only retrieval query in PREFLIGHT02_REVIEW.md is retained as method reference; it has already been used by the operator and need not be run again just to reproduce the evidence.

## Remaining correction review, without repeating passed tests

SQL03 is structurally ready for a separate approval decision, conditional on that focused watcher conclusion and review of its unchanged guards against the **saved02 output**. The grantor/options/column-state gap has already been closed by reported02 findings; do not reopen it or re-run passed registration, recovery, payment, survey or ACL preflights merely because this document is updated. If the actual metadata/state changes, stop and review the change; SQL03's saved-hash guards also fail closed rather than silently accept another state.

A subsequent separately authorised isolated PostgreSQL17.11 dummy rehearsal of exact unchanged03/05 logic now passes18 checks; only four documented local parameter literals differed. It closes the tested local syntax/transaction/inverse-state gap. See the rehearsal report linked from README.md. That rehearsal did not install/review real managed watcher bodies, connect to Supabase or run a production permission change; it does NOT close the watcher gate or justify repeating all previously passed functional tests. The full private watcher-body review remains OPEN.

After the remaining review, seek explicit approval for the exact SQL03 source and target snapshots, not a general instruction to launch. The observed baseline10fa... and original ACL digestfd7f... remain evidence, not approval; NOT_APPROVED/REVIEW_REQUIRED placeholders stay untouched. Retain original02 and later approved04 results for the separately guarded rollback05. No merge, worker deployment, delivery configuration, Stripe change or website publication follows automatically.
