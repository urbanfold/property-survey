# Single deployed diagnostic accept request — 2026-11-06

Owner approved one request only after reporting deployed diag-1 build, mode digest consistent with accept, and property/account rolling 24h event counts both 1. Those configuration/counter checks are owner-provided evidence.

Direct execution against hexhtduvqzleoazusskh only: authenticated confirmed dummy B, verified exact dedicated fixture 6 and its prior accepted submission. Updated only fixture 6 notes to `DUMMY F02 fixture 6 diagnostics accept check diag-1` and a fresh submission timestamp. Cloud readback confirmed both before notification.

Exactly one gateway notification POST, no retries:
- Start: 2026-11-06T12:27:18.145403+00:00.
- End: 2026-11-06T12:27:20.591336+00:00.
- Duration: 2.445 seconds.
- HTTP 200, status accepted.

Complete fixture row hash remained unchanged after notification. Original B property row hash matched before/after. No source, secret, deployment, production, credit, Stripe, Brevo, GitHub remote or cleanup changes made. Dummy Auth sign-in creates a normal test session. No original A records/rooms/photos were written.

Expected receiver diagnostic entries in 12:27:18–12:27:21 UTC window: build urbanfold-staging-receiver-diag-1, mode accept; events mode_selected then capture_committed; no timeout_wait events. Logs are not accessible through ordinary dummy credentials and remain owner-verification pending. HTTP accepted alone does not attest deployed build or exact-once capture.

Expected lifetime totals, pending private database reconciliation: 24 events, 23 accepted, 1 uncertain, 0 sending, 23 receipts, 23 capture attempts, 0 repeat-capture receipts. Preserve fixtures/evidence; no further request authorised by this run.

Machine-readable evidence: F02_DIAGNOSTIC_ACCEPT_EVIDENCE.json. One-use runner: f02_diagnostic_accept_once.py. Neither file contains passwords or tokens.
