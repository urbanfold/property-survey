# F02 survey notifications — STAGING VERIFICATION PASSED

Date: 2026-11-06. Project: Urbanfold-Survey-Staging, hexhtduvqzleoazusskh ONLY.
Scope: authenticated survey-notification gateway and dummy-only staging receiver; NOT registration notifications or production delivery. Existing development branch plan/security-remediation-2026-11-03, base HEAD ac15c68 with local uncommitted diagnostic/test/documentation changes. No commit/push/merge/deployment by the assistant is implied. Draft PR #1 is preserved; latest status remains owner-reported, not re-queried here.

## Final reconciled baseline

| Item | Final count |
|---|---:|
| survey_notification_events | 25 |
| accepted | 23 |
| uncertain | 2 |
| sending | 0 |
| captured survey receipts | 24 |
| committed survey capture attempts | 24 |
| receipts with repeated capture | 0 |

Evidence attribution: assistant directly executed authorised dummy A/B API tests and saved timestamped request/response/readback evidence. Private database totals and Supabase execution logs were inspected by the owner and supplied in this conversation; no management/database-owner access is held by the assistant. No independent inspection of production security is claimed.

Passed within tested scope: actual dummy Auth; cross-owner denial; unsaved/unsubmitted denial; recipient/actor override rejection; bounded request validation; receiver server-only auth; service-only receipt/outbox boundary; submitted success; sequential/concurrent deduplication with count reconciliation; changed-content/submission handling; five-property/twenty-actor cap responses; receiver rejection with saved-data preservation; diagnostic build/accept logs; actual deployed timeout-after-capture; restored-accept exact-revision duplicate without another capture. Original A/B survey rows and £6 allowances were checked unchanged during relevant direct runs. No customer data or actual emails were used.

## Timeout evidence

Diagnostic build urbanfold-staging-receiver-diag-1. Initial timeout request 2026-11-06 12:54:55.369983–12:55:07.378945 UTC: 202 uncertain, 12.008 seconds end-to-end. Owner receiver logs: 12:54:56 mode_selected timeout_after_capture; 12:54:57 capture_committed and timeout_wait_started; 12:55:09 timeout_wait_finished. Owner restored accept. One deliberately authorised exact-revision duplicate at 13:01:00.492657–13:01:02.338158 UTC: 202 uncertain in 1.844 seconds. Full fixture row/notes/timestamp unchanged. Owner confirmed no new receiver capture for that duplicate and final totals above.

Evidence retained: F02_DIAGNOSTIC_TIMEOUT_EVIDENCE.json, F02_TIMEOUT_DUPLICATE_EVIDENCE.json, their result reports and one-use scripts; F02_DIAGNOSTIC_ACCEPT_EVIDENCE.json; earlier f02-positive-evidence.jsonl and F02_DEPLOYED_STAGING_RESULTS.md under audits/2026-11-04; local diagnostic/SQL/application test logs and hashes under receiver-diagnostics. Preserve the initial unexpectedly accepted timeout attempt too; it is not evidence of a timeout pass. The diagnostic-enabled later test establishes the pass.

The two uncertain events are deliberately retained: dummy receiver guard rejection (no capture) and timeout after capture (one receipt). Do not reset/resend these events to make counts look accepted. No cleanup 008 was run. All six dedicated fixtures and prior synthetic Storage objects remain retained for review. Receiver mode accept restoration is owner-confirmed. No changes to production, Stripe, Brevo, GitHub Pages, credits or £179 service.

## Production release limits remain

- This is staging dummy capture, not real email/provider acceptance/delivery, a production deployment, or proof of live Supabase policies. Brevo/Zapier delivery and production configuration/metadata remain outside tested scope.
- HTTP accepted means accepted by transport, not guaranteed inbox delivery; uncertain events require reconciliation. No universal exactly-once external email guarantee.
- Actual 24-hour ageing/reset, simultaneous quota-boundary contention, scale/DoS and every worker-crash window were not tested against managed staging. Local SQL tests cover additional paths but are not cloud verification.
- Native managed-runtime behaviours are verified only along the observed requests. Full deployed source/rollback export has not been independently obtained; pre-change local copy is explicitly a rollback candidate, not a verified deployed snapshot.
- Diagnostic receiver is staging-only. Do not deploy it to production. Production requires separate review of the F02 gateway, migration003 effective metadata, secure real transport and secrets, external notification compatibility, release/rollback sequence and approval before any exposed legacy webhook rotation.
- Production signup email verification/password recovery success is owner-reported; production data isolation has not been independently retested by these staging results.
- Registration feature 004/dispatcher/006 is separate and is NOT marked staging passed. Its installation status must be checked read-only before proceeding.
- No merge, live publication, production SQL, secret rotation, fixture cleanup or new notification permission follows from this PASS.

Future registration capture tests must count receipts by kind='registration_verified', and preserve the above F02 baseline with kind='survey'. Whole-table receipt counts will include both kinds and must not be compared to 24 after registration testing begins.
