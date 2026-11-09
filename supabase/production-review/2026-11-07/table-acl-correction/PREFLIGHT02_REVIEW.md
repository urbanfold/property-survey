# Final SQL03 approval-readiness review — 7 November 2026

**READY FOR A SEPARATE APPROVAL DECISION; NOT AUTHORISED FOR EXECUTION.** The independent watcher behavioural review is complete. Upstream provider-version equivalence was not established. No production SQL or permission change was performed in this documentation update.

## Exact scope

Only these seven public tables: `properties`, `extensions`, `rooms`, `exterior_photos`, `extension_photos`, `sketch_photos`, `room_photos`.

Only `TRUNCATE`, `REFERENCES`, `TRIGGER`, `MAINTAIN` for `anon` and `authenticated`: **7 × 4 × 2 = 56 privileges**. One explicit REVOKE RESTRICT. Preserve SELECT/INSERT/UPDATE/DELETE, RLS policies, existing FKs/triggers, rows, private Storage, all credit tables, Stripe services, privileged-role grants and global default privileges.

TRUNCATE bypasses row filtering; the other three privileges enable unnecessary DDL/maintenance capability under their additional prerequisites. These are confirmed excessive database privileges, not proof of an exploitable arbitrary-SQL route through the normal PostgREST API.

## Previously saved production02 evidence

Project: `arnzqizcycesukplmvuc`.

- Original baseline: `10fa3ce6272648b31c662735e549b2e78b032a63cceb6e5f1d862f5d5052e4f6`.
- Original ACL snapshot: `fd7f49766854f09d849adee619f02054612ee1014aa63cbf6bfe3a53b7e6a861`.
- Exactly56 excessive grants, all direct postgres-issued and non-grantable; seven expected postgres-owned RLS-enabled tables with CRUD intact.
- No column ACLs; neither client role has SUPERUSER/BYPASSRLS; billing tables and storage.objects excluded.
- Recorded watcher fingerprints unchanged.

These are owner/connected-reviewer supplied results, not a fresh database query by this agent. Retain the full saved02 output privately. Recorded grantor does not establish the historical operator or prove that defaults caused the grants.

## Do the guards match?

**The reported grant/owner/RLS/column evidence matches SQL03's supported correction shape.** Before execution approval, the connected reviewer must confirm the remaining prerequisites in the already saved full02 output: PostgreSQL17+, trusted postgres session without simulated JWT, both client roles NOLOGIN, no owner inheritance, and no additional PUBLIC/delegated grant paths. The abbreviated owner results do not independently establish every one of these fields. Do not mark missing evidence passed by inference.

SQL03 checks approved action/acknowledgment, both exact accepted hashes, supported roles/table state, direct nongrantable grant shape, unsupported column REFERENCES/delegation paths and expected before/after ACL snapshots. It preserves the original baseline and requires all56 effective privileges denied before commit. Short lock/statement timeouts and RESTRICT fail closed. A guard/error rolls back the transaction; do not bypass it or retry automatically. A hash/label does not establish the actual connected project's identity.

The original baseline omits target non-row ACLs and can remain unchanged after correction. The separate ACL snapshot is required to verify the56-entry transition and rollback. Never replace a saved digest merely to make a guard pass.

## Completed watcher and local runtime evidence

[WATCHER_MANUAL_INSPECTION.md](WATCHER_MANUAL_INSPECTION.md) records the independent complete production control-flow review: catalog event inspection/filtering, temporary-object exclusions and fixed local PostgREST notification; no dynamic SQL, data/permission writes, external/network/email/payment actions or unreviewed user-defined calls. The previous OPEN behavioural requirement is satisfied on this supplied review. No authenticated upstream version comparison was performed; provider provenance remains unverified, not a blocker to the established behavioural conclusion for these definitions.

Commit `8710ff81df7249b92e7c37729f4cd9d77e14f773` contains the successful isolated PostgreSQL17.11 rehearsal: **18/18 checks passed**. Evidence: [report](../../../../audits/2026-11-07/acl-runtime-rehearsal/README.md), [results](../../../../audits/2026-11-07/acl-runtime-rehearsal/results.json), [parameterization](../../../../audits/2026-11-07/acl-runtime-rehearsal/parameterization.json).

Coverage includes56 removals, preserved CRUD/RLS/credit/Storage/dummy data, RESTRICT dependency mechanics, delegation rejection, failed-guard and post-REVOKE rollback, repeat-execution rejection and exact normalized ACL restoration. Only four documented parameter literals changed in local copies; production03/05 remained byte-identical. The native dummy run does not certify actual managed-platform locking, production runtime or upstream watcher provenance. No new rehearsal or SQL was run for this review.

## Frozen source and next action

SQL03 SHA-256: `625322c2f680faf0d0c8d2767519b71ab39fef0ed49999d7107bc99bfa5728cf`.

SQL05 SHA-256: `a19ad6bedf6fc9f5e253ceff9c1682f471ae45bbd6be11f072f110c0d2e1f5c8`.

Local byte comparison against reviewed commit `8710ff81df7249b92e7c37729f4cd9d77e14f773` confirms **both SQL03 and SQL05 are byte-for-byte unchanged**, including all four approval placeholders in each: `acl_ack` and `acl_action` remain `NOT_APPROVED`; `reviewed_baseline_sha256` and `original_acl_sha256` remain `REVIEW_REQUIRED`. No SQL/guard revision is proposed.

1. Independently inspect the saved02 remaining guard fields and confirm the target project, no intervening state change and an approved low-traffic window with no concurrent grant/schema changes. No repeat functional suite or repeated watcher retrieval is needed. If evidence is missing or drift suspected, obtain approval for only the targeted read-only check.
2. Request separate approval for exact SQL03 and the accepted baseline/ACL snapshot. Only that approval may authorise filling its four literals in a copy; record the parameterised copy hash. Run the complete transaction, never selected fragments.
3. After separately approved execution, use approved SELECT-only04 to verify all56 denied, CRUD/other ACLs and baseline preserved, and expected ACL transition. Retain02/04 evidence.
4. Any committed-change rollback requires separate SQL05 approval and the ORIGINAL02 ACL digest. Its inverse guard restores only56 original rights and refuses unrelated drift. Rollback restores excessive capability; prefer a reviewed forward fix when feasible. No automatic rollback or cleanup.

Backend migrations003/004, worker/email configuration, Stripe, merges and website release remain independent decisions. This report authorises none of them.

## Remaining risks and controlled verification

Readiness for a decision is not a claim that every live execution prerequisite has already passed. The saved production summary supports the grant shape; missing session/role fields must be checked in the full saved02 evidence. The actual future execution session must independently be confirmed as trusted postgres with no customer/simulated JWT, on PostgreSQL17+, connected to production project `arnzqizcycesukplmvuc`. Project text, staging-marker rejection and matching metadata hashes cannot independently authenticate the connected server. Do not change roles or weaken guards to proceed.

The rehearsal proves the tested isolated PostgreSQL17.11 behaviour, not zero downtime or identical managed-service locking. Coordinate a low-traffic window with no concurrent schema/grant changes. The advisory lock coordinates only operations using the same lock; it does not prevent arbitrary administrator changes. Short timeouts/dependencies may abort safely. Broad global defaults remain unchanged and could reintroduce excess rights on future recreated tables; future migrations need explicit object grants.

After a separately approved SQL03 execution, SQL04 must be explicitly authorised as the SELECT-only postflight. Compare its full saved output with original02: all56 effective high privileges false; every existing CRUD grant unchanged; same original baseline; exact expected ACL snapshot obtained by removing only the56 targeted entries; unchanged role/owner/RLS/column ACLs and credit/Storage/privileged-role ACLs. A different ACL digest alone does not prove correctness. Keep the original02 and postflight04 outputs and parameterised execution source/hash in the private release record. Postflight reads metadata, not customer row contents, and does not itself prove data contents or email/payment functionality; no fresh customer activity or broad functional retesting is implied.

If SQL03 fails before commit, its transaction rolls back; preserve the error and stop. If a committed change needs reversal, SQL05 is a separate security decision because it restores excessive capability. Independently reconfirm the production connection, obtain explicit rollback approval, and only then use its RESTORE action with the saved ORIGINAL baseline and ORIGINAL02 ACL digest. SQL05 requires all56 rights currently denied, reconstructs the original normalized ACL state and refuses unrelated drift before granting. It restores only those56 direct non-grantable rights; it does not restore data, defaults or other services. Retain rollback output and obtain approval for the read-only snapshot verification of exact original normalized ACL/baseline restoration. Never substitute the corrected ACL digest for the original or broaden grants to bypass a failure.

**Decision boundary:** this documentation commit/push approves publication of review evidence only. It does not approve SQL03, SQL04 or SQL05 execution, filling approval parameters, production/staging access, deployment, merging or website publication. Once saved prerequisites and connection checks are accepted, request a separate, explicit SQL03 execution decision.
