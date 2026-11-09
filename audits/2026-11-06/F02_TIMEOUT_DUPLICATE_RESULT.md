# Controlled exact-revision duplicate — 2026-11-06

Owner reported initial receiver logs: 12:54:56 mode_selected timeout_after_capture; 12:54:57 capture_committed and timeout_wait_started; 12:55:09 timeout_wait_finished; build urbanfold-staging-receiver-diag-1. Owner restored accept and explicitly approved one duplicate only, with no notes/timestamp edits.

Direct execution: confirmed dummy B Auth and exact full-row hash, notes and submission timestamp match the recorded initial timeout revision. Original B property hash also matched. Sent one gateway POST containing only fixture 6 property ID; no PATCH, new revision, retry, receiver direct call, secret edit or deployment.

- Started: 2026-11-06T13:01:00.492657+00:00.
- Finished: 2026-11-06T13:01:02.338158+00:00.
- Elapsed: 1.844 seconds.
- HTTP 202, status uncertain.
- Full fixture row hash and original B property hash unchanged afterwards.

Response is consistent with reviewed gateway's claimed=false / uncertain duplicate path, which bypasses receiver invocation. However, ordinary dummy credentials cannot independently inspect receipt table, capture counters or platform invocation logs. No-new-capture conclusion remains pending owner reconciliation: expected lifetime events 25, accepted 23, uncertain 2, sending 0; receipts 24, capture_attempts 24, repeated-capture receipts 0. No receiver mode_selected/capture_committed entries attributable to 13:01:00–13:01:03 UTC should exist.

No further request authorised or made. No cleanup, production/credit/Stripe/Brevo changes, commit, push or merge. Preserve all dummy evidence. Machine-readable evidence: F02_TIMEOUT_DUPLICATE_EVIDENCE.json; one-use script f02_timeout_duplicate_once.py; no credentials persisted.
