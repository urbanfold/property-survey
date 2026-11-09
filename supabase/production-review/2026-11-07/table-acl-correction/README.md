# Review-only correction: excessive client table privileges

**NOT APPROVED FOR EXECUTION.** Target production **arnzqizcycesukplmvuc**. Prepared from review commit **1d1c934ce39650433a58ec70640d4f3671ad018f**. The owner authorises this package's development-branch commit/push only. Original review preparation/publication executed no SQL. A subsequently authorised isolated dummy PostgreSQL rehearsal is recorded below; no production/staging SQL, permissions, data, services, secrets, Stripe, functions or website changes were made.

## Confirmed evidence versus uncertainty

**02 update:** read-only production preflight02 is reported passed. Original baseline remains `10fa3ce6272648b31c662735e549b2e78b032a63cceb6e5f1d862f5d5052e4f6`; observed ACL snapshot is `fd7f49766854f09d849adee619f02054612ee1014aa63cbf6bfe3a53b7e6a861`. All56 affected grants have recorded grantor postgres/grantable=false, all seven owners/RLS/CRUD are expected, and no column ACLs were found. SQL03 is structurally ready for separate approval review, NOT execution approval. Independent complete watcher behavioural review is now reported passed; upstream-version comparison was not performed. See [PREFLIGHT02_REVIEW.md](PREFLIGHT02_REVIEW.md) for the evidence boundary, remaining guards and safest private verification method.

The owner/connected reviewer reports read-only01 completed with unchanged observed baseline `10fa3ce6272648b31c662735e549b2e78b032a63cceb6e5f1d862f5d5052e4f6`. Both anon/authenticated have direct, non-grantable SELECT/INSERT/UPDATE/DELETE and TRUNCATE/REFERENCES/TRIGGER/MAINTAIN on seven postgres-owned, RLS-enabled tables: properties, extensions, rooms, exterior_photos, extension_photos, sketch_photos, room_photos. They do not inherit the owner and are neither SUPERUSER nor BYPASSRLS. The three credit tables lack these four extra client privileges. All five billing bodies match; all nine foreign keys are valid/cascading; public.rls_auto_enable() is absent. These are owner-supplied findings, not a new direct production inspection by this development agent.

The previous01 ACL expansion did not include grantor. Broad global defaults are a possible explanation, NOT proven grant provenance. The completed02 query captures **recorded grantor role**, grant options and column ACLs; its reported grantor/options/column findings now match the supported correction shape. Even recorded grantor=postgres does not identify an original human, date or whether defaults produced the grant. Independently inspect the saved full snapshot/remaining guards and retain the completed private watcher behavioural conclusion before deciding execution approval.

## Security assessment and scope

- TRUNCATE operates on whole tables and is not constrained by RLS row policies. Lack of BYPASSRLS does not make this privilege harmless.
- REFERENCES can permit FK construction/probing where a caller also has the necessary DDL/schema access; it does not itself grant SELECT. RLS does not protect REFERENCES in the way it protects row operations.
- TRIGGER permits creating triggers with the additional required function/DDL permissions. Existing trigger execution does not require customers to retain this table privilege.
- MAINTAIN permits maintenance operations on supported PostgreSQL versions; it is not required for app CRUD and can create availability/operational risks.
- PostgREST's normal table API does NOT expose arbitrary SQL/TRUNCATE/DDL. These grants prove excessive database capability, not an already-demonstrated unauthenticated HTTP exploit, compromise or data loss. Reachability through any other SQL/RPC path affects exploitability. No exploit/probe or destructive test was run.

Recommended correction: revoke **only** those four table privileges from **only** anon and authenticated on the seven named tables, using **RESTRICT**. Preserve their CRUD grants exactly and leave RLS to continue enforcing row ownership. Preserve all postgres/service_role rights, existing FKs/triggers/functions, Storage ACLs, credit tables and global/default/schema/sequence/function privileges. Do not apply001/002, blanket-revoke ALL, revoke PUBLIC broadly, use CASCADE, change roles or alter defaults as a shortcut.

Existing FKs remain valid: REFERENCES is checked when creating constraints, not a new permission requirement for ordinary DML using an existing FK. TRIGGER is for creation, not a permission customers need when existing allowance/address triggers fire. Normal survey saving, uploads, exports and Stripe credit handling use CRUD/RPC/Storage paths, not these four privileges. This is source/permission reasoning, not a fresh runtime test; no functional SQL was executed in this preparation.

## Files / review sequence

1. **02_acl_preflight_readonly.sql** — SELECT-only metadata. Same original baseline algorithm plus a NEW independent ACL snapshot/digest. Includes target table/column ACLs with grantor/options, CRUD, roles/owner-inheritance flags and untouched Storage/credit ACLs. No data rows, Auth users, raw watcher bodies, secrets or network calls.
2. **03_revoke_excess_table_privileges.sql** — one transaction and one explicit REVOKE covering the seven tables/two roles/four rights. Disabled approval parameters, exact reviewed hashes, owner/role/RLS/CRUD/column checks,56 direct supported entries, RESTRICT and before/after invariants. No database helper/audit table is installed.
3. **04_acl_postflight_readonly.sql** — SELECT-only same snapshots/digests/effective permissions. All56 effective excess-access checks must be false after approval/application; CRUD/other ACLs and original baseline must be unchanged.
4. **05_restore_exact_previous_privileges.sql** — independently approved rollback, not routine cleanup. Reconstructs only the56 known former direct entries; refuses unless that inverse snapshot matches the saved ORIGINAL02 ACL digest. No grant options, PUBLIC grants or service/billing changes. Restores the security risk, so forward repair is preferred where possible.
5. **SOURCE_SPEC.json**, **SHA256SUMS.txt** — scope/source and file integrity. The generator `scripts/build_table_acl_review.py --check` is source-only and never executes SQL. Static/model tests and limitations are in audits/2026-11-07/table-acl-correction.

## Why a new ACL fingerprint is necessary

The original baseline metadata records legacy table **CRUD** and existing function/default ACLs, not the four target non-row table privileges. Therefore this correction can leave baseline10fa... UNCHANGED. That digest alone cannot certify the correction or its rollback. Save/review the full02 `acl_snapshot` and `acl_sha256`, independently of the baseline. The snapshot sorts ACL grantor/grantee/privilege/options and includes roles, RLS/owner, CRUD, column grants and untouched credit/Storage table ACLs. It intentionally does not read customer/credit rows.

The observed02 ACL digest is now recorded above, but no observed digest is silently approved or prefilled into SQL. All executable files retain NOT_APPROVED/REVIEW_REQUIRED. Project-name text/GUC acknowledgements and hashes are NOT independent connection-identity verification; the connected reviewer must confirm the actual production project before even approved SQL.

## Preconditions / supported state

- Trusted postgres owner session, no customer/simulated JWT; PostgreSQL17+ (MAINTAIN supported); independently confirmed production. Known staging marker is rejected. Two client roles must exist and not be login/superuser/BYPASSRLS/owner-inheriting roles. Unexpected attributes cause STOP, not role changes.
- All seven targets are existing postgres-owned, RLS-enabled ordinary tables, with current CRUD grants intact for both roles. Force-RLS state is preserved, not toggled.
- Exactly56 relevant grants must be direct, recorded-grantor postgres and non-grantable. PUBLIC high grants, another grantor, grant options, grants delegated by client roles, explicit client/PUBLIC column-level REFERENCES, partial prior correction or missing objects cause STOP. Do not SET ROLE to an unknown grantor or use REVOKE CASCADE to get past it. Prepare a separately reviewed provenance/column/dependency-specific proposal if this state differs.
- Global/default privileges are not modified. A later table recreation can reintroduce broad defaults; future migrations must explicitly restrict their own new objects. Existing003/004 already explicitly revoke ordinary-role rights on their new private tables.
- Review the two provider/PostgREST watcher definitions privately first (below). Use one operator/no concurrent grant/schema changes and a low-traffic approved window. Short lock/statement timeouts fail rather than silently wait or retry; customers may continue using existing rows, but no zero-lock/downtime guarantee is made without a runtime rehearsal.

## Watcher review and remaining uncertainty

**Independent behavioural review COMPLETE:** see [WATCHER_MANUAL_INSPECTION.md](WATCHER_MANUAL_INSPECTION.md). The reviewer inspected complete production definitions and calls: catalog-event filtering, temporary-object exclusions and fixed PostgREST schema-cache NOTIFY only; no dynamic SQL, permission/data writes, external/email/payment operations or unreviewed user-defined calls. Earlier partial inspection is superseded by this supplied independent conclusion.

Recorded fingerprints remain ddl `de987df746eb39647098459e7993bd8595e592969b0cd647828a3d13d37cffe0` and drop `791b41f0632fc86e0fc86a303ec0fd710c4e2ecf947a23422dae2b7a2c122f1d`. Both were reported enabled, supabase_admin-owned SECURITY INVOKER with empty search paths. No authenticated upstream Supabase version comparison was performed; provider identity/version equivalence is not certified. Changed definitions require review. No watcher changes or repeated retrieval are recommended.

## Future application sequence — requires separate approval

1. The owner reports02 already completed read-only. Review and retain that saved result; do not repeat it merely to reproduce passed evidence. Retain the completed independent watcher-body conclusion and inspect the remaining guards before any execution decision. If a changed/stale state requires a new02, separately authorise that read-only check through the connected integration. Compare reported baseline with original10fa...; any difference requires exact review. Accept grantor/options/columns/role flags and private watcher conclusions; save full snapshots securely. No global defaults or other permissions change at this step.
2. Obtain independent approval of exact03, the actual connection and observed metadata. Fill only these four parameter literals in a copy of03:
   - urbanfold.acl_ack: `APPROVED arnzqizcycesukplmvuc TABLE ACL REVIEW 1d1c934ce39650433a58ec70640d4f3671ad018f`
   - urbanfold.acl_action: `APPROVED REMOVE56 EXCESS PRIVILEGES`
   - urbanfold.reviewed_baseline_sha256: accepted current original-baseline digest.
   - urbanfold.original_acl_sha256: accepted02 ACL snapshot digest, never the baseline digest.
   Record the actual parameterised file hash/approval. Do not edit guards/privilege lists or run a selected section.
3. Only after that approval apply03. Inside the single DO/transaction it captures before state, derives the expected after snapshot by removing exactly56 entries, performs one REVOKE RESTRICT, verifies baseline unchanged and exact expected after snapshot, and checks all56 effective rights are false. Any exception/dependency/inherited path/side-effect mismatch rolls back the entire transaction. No automatic retries or broad fallback.
4. Run approved04. Confirm all56 allowed=false, original baseline unchanged, expected ACL digest transition, all CRUD unchanged, privileged-role/column/Storage/credit ACLs unchanged. Keep service/credit/record evidence; no test payment or new survey is required to inspect permissions. A later explicitly approved normal operation check can use a controlled account; do not rerun passed broad suites or create customer activity by assumption.
5. Treat this as a separate reviewed privilege-hardening record, not a claimed migration-history repair. Existing003/004 installers still need separate final approval; correction does not authorise their installation, worker deployment, scheduling or frontend release.

## Reversibility / failure recovery

Before commit, any guard/RESTRICT/postcheck error rolls back03 automatically. Preserve the error without secrets and stop; do not drop dependent objects, widen grants or change defaults to make it pass.

If a committed correction requires rollback, obtain separate approval for05. Stop concurrent grant/schema changes; verify the same project. Use the same saved ORIGINAL baseline and ORIGINAL02 ACL digest, same acknowledgement, but action must be `APPROVED RESTORE56 ORIGINAL PRIVILEGES`.05 requires all56 effective rights currently false. It adds exactly the56 former grantor=postgres, grantable=false entries to an in-memory expected snapshot and demands its digest equals the saved original. Unrelated state changes or unsupported original provenance therefore stop rollback before GRANT. It grants just those four rights to the two roles on the seven tables, then verifies semantic ACL snapshot equality with the original and unchanged baseline. Logical grantor/options/rights are restored; no promise of binary ACL-array ordering or historical grant timestamps is made. Never GRANT ALL/WITH GRANT OPTION, restore defaults or modify a saved hash to force rollback.

Rollback intentionally restores excessive privileges; it is not a desirable steady state. A later different schema/role/ACL state requires a new reviewed forward correction or rollback, not ad-hoc broad grants. No data restore, table drop, credit reset, Storage deletion or customer-record modification belongs to this package.

## Local runtime rehearsal update / remaining limitations

**Authorised local rehearsal PASSED on PostgreSQL17.11:** exact unchanged03/05 logic with only four documented local test parameter values. All18 recorded checks passed:56 removals, CRUD/RLS/Storage/credit/dummy-data preservation, RESTRICT mechanics/delegation rejection, failed guards and post-REVOKE rollback, repeat rejection and exact normalized ACL restoration. See [rehearsal report](../../../../audits/2026-11-07/acl-runtime-rehearsal/README.md), results.json and parameterization.json. Production originals remain byte-identical. One rehearsal-only startup readiness error was corrected; no production-script correction is proposed.

The previous preparation used static/Python-model checks only; that historical evidence is retained rather than overwritten. The new native rehearsal closes the local SQL-runtime gap, not actual managed-service/provider verification. The disposable cached-image container used network none, no published ports/host mounts/forwarded secrets, tmpfs data and fabricated records/roles; it was removed. No actual Supabase project was contacted. The independent production watcher behavioural review is now reported complete, separately from the local rehearsal; no authenticated upstream-version comparison was performed. A synthetic local failure handler does not validate managed watcher bodies. Actual production drift/roles/grants and execution approval remain separate checks. No production03/05 execution, merge or website publication is authorised by these test results.
