# Diagnostic timeout: initial request only — 2026-11-06

Owner approved one initial request after reporting timeout mode saved and pretest counts: 24 events, 23 accepted, 1 uncertain, 0 sending, 23 receipts/attempts, zero repeats; property/account rolling counts both 2. Owner deployed diagnostic build diag-1 previously. No assistant deployment or setting change.

Fresh dummy B Auth verified and exact dedicated fixture 6 matched its last accepted revision. Only fixture 6 notes (`DUMMY F02 fixture 6 diagnostic timeout check diag-1`) and submission timestamp were updated; both read back before request.

Exactly one gateway notification request, no retry:
- Started 2026-11-06T12:54:55.369983+00:00.
- Finished 2026-11-06T12:55:07.378945+00:00.
- HTTP 202, status uncertain, elapsed 12.008 seconds (end-to-end including gateway Auth/DB/receiver/finish operations).

Complete saved fixture row and original B property row hashes matched before/after the request. No original A properties, room/photo records, credits, Stripe, Brevo, production, GitHub refs or cleanup altered. No duplicate request sent; further request remains gated on operator restoration to accept.

This is the expected gateway response but not yet a complete timeout verification. Owner must inspect receiver logs for build urbanfold-staging-receiver-diag-1, mode timeout_after_capture, events mode_selected/capture_committed/timeout_wait_started around 12:54:50–12:55:20 UTC. A later timeout_wait_finished may appear; it is not a prerequisite to a committed receipt. Restore accept and confirm before deliberate duplicate request. Privileged ledger/receipt verification remains pending; expected totals 25 events, 23 accepted, 2 uncertain, 0 sending, 24 receipts, 24 capture attempts, zero repeated captures. Expected same after a later separately permitted duplicate check.

Evidence: F02_DIAGNOSTIC_TIMEOUT_EVIDENCE.json. One-use script: f02_diag_timeout_once.py. No tokens/passwords persisted. No app source changes, secret edits, deployments, pushes, merges or cleanup performed by the assistant.
