# F02 deployed staging checks — 2026-11-04

Target: `hexhtduvqzleoazusskh` only. Source reviewed/tested against: local `ac15c68`.
Remote refs checked read-only: main `6874d8ab034df341bb6c32f21f1b94f3279f224b`, development branch `1715020d53b72b084563b89abed419c93c86bf09`. Local HEAD has two unpushed commits (`f855073`, `ac15c68`), plus the uncommitted test/report/fixture preparation from this check. No push or deployment performed. Deployed source revision cannot be independently attested through ordinary-user API access; behavioural checks below exercise the actual deployed endpoints.

## Owner-reported prerequisites, not independently audited cloud metadata

005 installed, all eight metadata/security checks passed; both Edge Functions deployed with reviewed JWT settings and five staging configuration settings. Receiver accept mode, gateway staging_capture, registration disabled, payments disabled. Owner's pre-test receipt_rows=0 and capture_attempts=0. No service-role or management credential available to the tester.

## Direct tests completed

Runner: `staging-check-tools/f02_deployed_checks.py`, uses securely supplied dummy credentials, exact staging HTTPS host only; no tokens/passwords saved. All 24 assertions passed (20 HTTP boundary cases plus two identity/fixture and two allowance assertions):

- A/B real password login matches expected immutable Auth UUID; exactly one visible own property each, original fixture still unsubmitted.
- Unauthenticated POST and invalid bearer POST: 401.
- B requesting A, and A requesting B: 403.
- Each own saved-but-unsubmitted survey: 409; nonexistent/unsaved property: 403.
- Caller-supplied recipient and actor fields: 400; oversized body: 400.
- Unapproved Origin: 403; localhost:8794 preflight: 200; GET gateway: 405.
- Receiver rejects A JWT, B JWT and anonymous POST: 401.
- A/B direct reads of receipt table and private notification outbox: 403.
- Both allowance responses still report price_pence=600, paid_credits=0, can_create=false.

No property mutation, submission timestamp update, fixture creation, successful notification claim, capture or payment was attempted. Dummy sign-ins create normal Auth sessions. No original surveys, photographs or customer records changed. There is no fixture cleanup required from these tests.

## Boundary and outstanding tests

Ordinary dummy credentials deliberately cannot read receipt/outbox counts or create additional properties without credit. Therefore successful delivery/capture, saved recipient selection, duplicate suppression/concurrency, actual rolling rate limits and transport failure recovery are NOT yet verified against the deployed system. A success/duplicate HTTP response alone would not prove single capture; owner-only receipt counts/attempts must also be compared.

Do not bypass RLS, add paid credits, submit the original A/B surveys, or use production keys to solve this boundary. Prepared but NOT executed: `supabase/staging/007_f02_dedicated_test_fixtures.sql`, adding six new clearly labelled dummy properties through the existing postgres maintenance exemption, asserting free allocations and purchases unchanged. This does not test the customer credit creation path or relax that rule. It allows four A properties × five changed submissions to exercise the 20/day actor cap and a fifth A property to verify actor rejection separately; B has a separate fixture. No table/policy/function/secret changes. Original A/B records remain separate.

The SQL script includes staging comment and exact confirmed dummy identity guards, but these do not cryptographically bind a database to a project: the operator must verify the Dashboard reference before running. It refuses re-execution if its dedicated IDs already exist. Local preparation was inspected; it has NOT been executed or runtime-validated on staging.

Run `supabase/staging/f02_read_only_counts.sql` before positive testing and afterwards. This provides counts only and does not reveal payloads or recipients. Counts currently remain owner-reported; denial responses and source paths strongly indicate no capture from this run but do not independently prove unchanged totals.

## External delivery and residual risks

The Python runner contacts only the staging Supabase host. All tested requests fail before notification claim/transport. Reviewed staging_capture source uses only the same-project receiver and REST APIs; it does not call SMTP, Brevo, Zapier, Stripe or production. This run did not exercise outbound delivery, and ordinary-user API access cannot inspect deployed secrets/source or egress logs, so an absolute independent attestation of server egress is not claimed.

For positive tests retain exact dummy payloads/receipts and event states for review. A/B cannot delete parent properties under the existing policies; owner cleanup must be exact-ID scoped after evidence is recorded. Deleting a property cascades its notification events, so do not prematurely delete evidence. Do not deploy an extra privileged test endpoint merely to obtain counts.

Receiver rejection/timeout fault-injection modes require an explicitly reviewed staging configuration change; no settings were changed in this run. Uncertain deliveries intentionally do not automatically resend and require operator reconciliation. Registration notifications (004/worker) remain outside this test, uninstalled/undeployed by the assistant. £179 service remains separate from £6 credits.

## Dedicated positive phase — direct endpoint results

The owner executed 007 and supplied starting totals: six dedicated properties, zero events/receipts/capture attempts. The assistant then exercised only the six exact `f0200000-0000-4000-8000-000000000001`–`006` fixtures. Full timestamped safe response evidence: `f02-positive-evidence.jsonl`; runner: `staging-check-tools/f02_positive_checks.py`. The runner is intentionally single-use and refuses to overwrite existing evidence; do not rerun against partially consumed rate limits. Extra post-run tests changed only fixture 4's submission timestamp, confirmed unchanged-content deduplication at the account cap, and checked foreign ownership on the dedicated fixtures.

Observed deployed behaviour:

- A first valid submitted request returned HTTP 200 accepted; a sequential repeat returned accepted.
- Four simultaneous FIRST requests for fixture 2 returned one 200 accepted and three 202 uncertain while claim processing was in progress. A subsequent request returned accepted. Response status alone cannot prove exactly one receipt; private counters below must confirm it.
- Modified content retaining an already-used submission timestamp returned 409. The same changed content with a new saved timestamp returned 200 accepted.
- Property 1 allowed five distinct notifications and rejected its sixth changed submission with 429. Saved blocked edits were still present.
- Four A properties allowed five distinct submissions each (20 total); unused A fixture 5 then returned 429. This exercises both rolling-window caps for events created now. Actual 24-hour ageing/reset and concurrent limit-boundary contention were not exercised against cloud staging; no timestamps were backdated.
- After the account cap, fixture 4's unchanged content with a refreshed submission timestamp returned 200 accepted, consistent with fingerprint deduplication before quota accounting.
- B's reserved dummy address was deliberately uppercased to `@EXAMPLE.INVALID`. It remains a non-deliverable reserved domain, but fails the receiver SQL's case-sensitive guard. The gateway returned 202 uncertain; repeating it also returned uncertain. The property and saved submission remained available. This tests actual receiver-side guard rejection, NOT the configurable simulated 503 rejection mode.
- A changed B submission with the corrected lower-case dummy recipient returned 200 accepted. A malformed saved recipient returned 409, then the dummy recipient field was corrected without sending another notification.
- B cannot request A's dedicated fixture and A cannot request B's dedicated fixture (403).
- SHA-256 comparisons of complete original A/B property rows before/after matched. Both complete allowance responses matched (600-pence price, no paid credits). No original room/photo records were written.

Expected private ledger after these requests, pending SQL verification:

| Fixture | Events | Accepted | Uncertain | Receipts | Capture attempts |
|---|---:|---:|---:|---:|---:|
| 1 | 5 | 5 | 0 | 5 | 5 |
| 2 | 5 | 5 | 0 | 5 | 5 |
| 3 | 5 | 5 | 0 | 5 | 5 |
| 4 | 5 | 5 | 0 | 5 | 5 |
| 5 | 0 | 0 | 0 | 0 | 0 |
| 6 | 2 | 1 | 1 | 1 | 1 |
| Total | 22 | 21 | 1 | 21 | 21 |

The receiver's rejected SQL invocation should not insert a receipt: `capture_attempts` counts committed capture RPC successes, not failed HTTP receiver invocations. Every retained receipt should have attempts=1; there should be no `sending` event. Exact duplicate-delivery conclusions remain pending these privileged counts. Prepared read-only query: `supabase/staging/f02_positive_read_only_evidence.sql`.

No timeout was induced. No privileged credentials are available to change `STAGING_RECEIVER_BEHAVIOUR`. To exercise the deployed gateway's 10-second timeout against a receipt captured before the receiver's 12-second delayed response, the operator must set that staging-only value to `timeout_after_capture`, then the tester can send a new B fixture revision and repeat it. Afterwards restore `accept`. The separate configured `reject` mode also remains untested; current real guard rejection does not establish behaviour for all network/transport failures. Three additional B events remain available under the current property cap for controlled follow-up tests.

The runner sent HTTPS traffic only to the exact staging host. Reviewed capture SQL has no external delivery code and deployed gateway behaviour is consistent with the owner-confirmed capture-only configuration. Server egress logs and deployed secret values are not visible to this tester, so independent proof of every server outbound request is not claimed. No live recipient, production credential, payment call, new function deployment, setting change, cleanup, push or merge occurred. Evidence and all six fixtures remain for review. Main/development remote refs remain unchanged at the values recorded above.
