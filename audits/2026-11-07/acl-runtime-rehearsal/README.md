# Isolated ACL03/05 PostgreSQL rehearsal — 7 November 2026

**RESULT: PASSED on PostgreSQL17.11. Production/staging untouched. Full managed PostgREST watcher-body review remains OPEN.** This closes the local runtime-rehearsal gap only; it does not authorise a production permission change or claim native Supabase/provider integration verification.

## Exact sources and isolation

Reviewed branch source:061bff14b887fa4ba03c785ccf2c82cf84a9158e. Production originals are byte-identical before/after:

-03_revoke_excess_table_privileges.sql:625322c2f680faf0d0c8d2767519b71ab39fef0ed49999d7107bc99bfa5728cf
-05_restore_exact_previous_privileges.sql:a19ad6bedf6fc9f5e253ceff9c1682f471ae45bbd6be11f072f110c0d2e1f5c8

The runner `tests/test_table_acl_rehearsal.py` uses the explicit local Unix Docker socket, a previously cached/pinned official PostgreSQL17 image and `--pull never`. It forwards only minimal CLI configuration to an empty temporary Docker config directory; no host credentials, Supabase/Stripe/Brevo environment or HTTP clients are used. The container has network none, no published ports, no host bind/volume mounts, tmpfs data, resource limits, and the dedicated database urbanfold_acl_rehearsal. SQL reaches only that container's Unix socket via docker exec. The runner verifies current_database/current_user/server version/Unix-socket connection and inspects network/mount/port/environment isolation before fixtures. Host Docker availability is not permission to use a remote Docker daemon or another SQL connection.

POSTGRES_HOST_AUTH_METHOD=trust is confined to this unreachable, ephemeral test cluster; it changes no host or Supabase authentication settings and requires no password. The container/tmpfs data and temporary CLI configuration were removed after testing. Native result reports server170011/PostgreSQL17.11; cached image digest/ID and isolation assertions are in results.json. No image download occurred.

## Every local fixture adaptation

`LOCAL_ONLY_fixture.sql` is the generated exact setup input, retained for inspection and hash verification. NEVER execute it on Supabase. It begins with a local database-name/Unix-socket assertion. It derives from the existing isolated tests/database_fixture.sql, with only these construction adaptations before canonical001/002 setup:

1. The legacy properties.user_id FK plus five property-child and one room-child FK use ON DELETE CASCADE. Source table references are schema-qualified. Combined with the two canonical002 Auth FKs, the dummy schema has nine validated/cascading FKs.
2. Only extensions.width/length change in the dummy fixture text from numeric to numeric(5,2), matching the reported precision. Production types are not altered.
3. Broad postgres/public TABLE/FUNCTION/SEQUENCE default grants are created ONLY in the dummy cluster, modelling the provider-style defaults whose preservation must be checked. Actual production defaults are not fetched or changed.
4. Unchanged canonical001/002 are executed ONLY to construct local RLS, private Storage metadata, payment/allowance helpers and triggers. This is not an installation against either Supabase project and does not use staging setup/seeds.
5. The seven dummy targets grant ALL to local anon/authenticated/service_role without grant options; anon/authenticated are NOLOGIN, no superuser/BYPASSRLS. service_role has its normal test-only bypass flag. Existing required schema/Storage privileges are dummy grants. Two extra NOLOGIN probe/delegate roles support negative tests.
6. Two fabricated Auth IDs, two fictional houses, one extension/room, synthetic photo URL rows/Storage metadata, a free-allocation row and one synthetic600p purchase are seeded. IDs/emails are generated test constants and example.invalid; no real account or customer data is copied. `cs_live_LOCALDUMMY`/`pi_LOCALDUMMY` are fake local ledger strings, not payments, tokens or Stripe calls. There are no email transports, pg_net, Stripe connection or native managed watcher implementations.

A separate dummy probe table/ACL chain and an intentionally malicious **LOCAL** event-trigger fixture are created for specific negative cases; they are not representations of the real PostgREST watchers. They never make network calls. Their creation/removal is test-fixture work only.

## Exactly four parameter changes per test copy

Production files remain unchanged. In memory, each execution copy changes ONLY these four SET LOCAL value literals:

-urbanfold.acl_ack: the exact acknowledgement text already required by the original guard. Its production-project label is an opaque guard constant here, NOT a claim of production approval or connection identity; container/database isolation proves the test target.
-urbanfold.acl_action: original exact REMOVE56 or RESTORE56 acknowledgement; wrong-action negative case deliberately supplies the other action and must fail.
-urbanfold.reviewed_baseline_sha256: freshly computed LOCAL metadata digest; wrong-hash test supplies zeros and must fail.
-urbanfold.original_acl_sha256: freshly computed LOCAL original snapshot digest; wrong-hash test supplies zeros and must fail.

`parameterization.json` records every copy's original/copy SHA256, exact replacement map and unified diff. Reverse substitution is asserted to reproduce the original byte-for-byte. No guard, SQL body, privilege target, RESTRICT, role, metadata function or approval requirement is removed/replaced. There is no mock of digest/permission checks. Production's actual10fa... baseline/fd7f... ACL digest are explicitly forbidden as local parameter values. Unedited sources are also executed as negative cases and must refuse approval. The user's explicit authorisation covers these LOCAL rehearsals only, not production acknowledgement.

## Results and interpretation

All18 recorded checks passed; setup/isolation and source-integrity checks are included in that count. See results.json and run.log for exact case names.

-Actual unchanged03 logic removed all56 effective target rights. Native has_table_privilege returned false for every combination. Baseline metadata digest stayed unchanged while the independent ACL digest changed, as designed.
-All existing CRUD, RLS/owner/role metadata, column ACLs, privileged-role entries, Storage/credit ACLs and dummy data hashes were preserved. Representative authenticated local RLS/DML, room/photo operations and allowance-trigger insertion succeeded inside an explicitly rolled-back transaction. Anonymous property reads remained blocked; an owner could see only its own dummy property. These use local synthetic claims, not a genuine Supabase login/API or production permission proof.
-Unedited sources, wrong baseline/ACL/action, repeated03 and repeated05 failed closed with no state changes. Wrong original rollback hash and an unrelated Storage ACL change prevented05 from restoring over another state.
-An artificial LOCAL REVOKE event handler granted an unrelated probe SELECT during03. The original postcheck detected the unexpected ACL; the exception rolled back BOTH the56-right removal and the probe grant. Real watcher bodies were neither installed nor validated by this test.
-Actual unchanged05 logic restored the complete normalized original ACL snapshot, original metadata digest, all56 original effective privileges and identical dummy data. Logical grantors/options/rights match, not an assertion about historical grant timestamps/binary ACL array ordering.

### RESTRICT dependency nuance

The exact script's valid supported state forbids client grant options/delegation, so a normal downstream client-grant chain is rejected BEFORE its REVOKE. That precondition was tested with a deliberately delegated target grant:03 refused it unchanged; the guard was NOT weakened to force the REVOKE.

Separately, PostgreSQL's REVOKE TRIGGER ... RESTRICT was exercised on a dedicated out-of-scope local probe table with a real downstream grant. It returned2BP01 (dependent privileges exist), preserving the grant chain/data. This verifies actual PostgreSQL RESTRICT semantics, but is not misreported as an in-script dependency failure under the valid56-entry shape. No CASCADE fallback was used. Existing nine FKs also remained unchanged during successful03/05.

## Initial harness-only failure and correction

The first attempt stopped before dummy setup/script execution because pg_isready accepted the image's temporary init server before POSTGRES_DB existed. The connection to the dedicated dummy database failed. The local container was removed; no03/05 was attempted in that run. Initial log/results are preserved as attempt1-startup.*.

Only the rehearsal runner was corrected to wait for the official init-complete marker AND a successful real SELECT1 in the final dedicated database. A new isolated container was then used for the full successful run. No production SQL/script/guard correction was needed or made. No failed runtime result was reclassified as passed.

## Reproduce or fall back safely

With authorised LOCAL SQL testing, cached pinned image and a local Unix Docker socket:

```text
python -B tests/test_table_acl_rehearsal.py
```

This starts/removes only a uniquely named test container; it does NOT use database URLs or host psql. It writes local evidence files, so preserve this run before another authorised reproduction. If Docker/image/local isolation is unavailable, do not pull arbitrary images, publish ports, mount a real data directory, connect to an existing database, substitute Supabase credentials or weaken the safety checks. Use this documented procedure for later review without executing SQL. No runtime test is required merely to repeat already passed evidence.

## Remaining limits / proposed corrections

**No correction to production03/05 is proposed.** Native SQL syntax/transactions/guards/inverse behaviour pass in this dummy PostgreSQL17.11 fixture. The one necessary correction was rehearsal startup readiness only.

Full actual managed watcher-body review remains OPEN. Neither positive NOTIFY observations nor this artificial handler test proves all provider control flow/indirect calls are safe. Native Supabase Auth/Storage/Edge execution, real grants/data/state drift, managed platform events and future versions were not tested. A current saved production02 state, privately completed watcher review and separate explicit approval for unchanged03 remain necessary before any production action. No merge, push, deployment, production/staging SQL, permissions, secrets, Stripe, real email or customer data change is authorised by this rehearsal.

## Separately authorised evidence publication

After reviewing the local results, the owner separately authorised committing/pushing this evidence to plan/security-remediation-2026-11-03. This publication does not authorise new SQL, production access, permission changes, deployments, merge or website release. Included files are plain-text reports, original input fixture source, parameter diffs and runner code; LOCAL_ONLY_fixture.sql is a synthetic setup input, not a database dump. No container image/filesystem/volume, container ID, customer data, credentials or environment-variable dump is included. Generic local socket/database labels and public pinned-image identifiers/version are retained for reproducibility, not sensitive host environment details. The original results and initial harness-error evidence are preserved.
