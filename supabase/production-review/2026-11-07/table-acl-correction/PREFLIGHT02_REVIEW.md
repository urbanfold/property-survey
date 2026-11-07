# Production ACL02 evidence and SQL03 readiness — 7 November 2026

**Structurally ready for a separate independent approval review; NOT approved for execution. Limited manual watcher inspection is recorded; full watcher-body verification remains OPEN.** This is a documentation/evidence update only. SQL02/03/04/05, generator, approval placeholders and application/runtime code remain unchanged from f4c08465fd750444a9b40ff57a6d52f96557ccaa. No SQL, permission change, rollback, deployment, notification, Stripe operation or website release was executed by this development agent.

## Owner-reported read-only evidence

Project: arnzqizcycesukplmvuc. The owner reports production02 completed successfully and gives:

- Original baseline unchanged: `10fa3ce6272648b31c662735e549b2e78b032a63cceb6e5f1d862f5d5052e4f6`.
- Observed ACL snapshot SHA256: `fd7f49766854f09d849adee619f02054612ee1014aa63cbf6bfe3a53b7e6a861`.
-56/56 effective excessive privileges currently allowed; seven expected postgres-owned, RLS-enabled tables with CRUD intact.
-All56 affected grants recorded with grantor postgres and grantable=false.
-No column-level ACLs found; neither client role is SUPERUSER/BYPASSRLS.
-The three credit tables and storage.objects are outside the correction.
-Both PostgREST watcher fingerprints remain unchanged.

These are supplied results, not a live query or independent hash recomputation by this agent. Full raw02 metadata is not pasted here; the approving reviewer should retain and inspect that original output securely. A snapshot digest does not prove historical grant attribution, function behaviour or execution approval. The recorded grantor role does not identify the original person/time/default mechanism.

Grantor/options/column-state evidence requested in the original package is now supplied. The old findings/results files remain historical preparation records; this update supersedes their “not yet captured” status without overwriting that evidence. Neither observed hash is automatically approved or filled into a script.

## Structural assessment of unchanged SQL03

SQL03 SHA256: `625322c2f680faf0d0c8d2767519b71ab39fef0ed49999d7107bc99bfa5728cf`.

The supported shape now agrees with the reported grant evidence. One explicit REVOKE RESTRICT targets only TRUNCATE/REFERENCES/TRIGGER/MAINTAIN for anon/authenticated on the seven named tables. No global defaults, CRUD grants, RLS, privileged-role access, Storage/billing ACLs, FKs or rows are changed by that statement.

The file still starts with a transaction, short timeouts and NOT_APPROVED/REVIEW_REQUIRED parameters. It verifies the separately accepted baseline and original ACL snapshot, owner/RLS/roles/CRUD state and direct non-grantable entries; refuses unsupported PUBLIC/other-grantor/delegated/column REFERENCES cases; derives an expected snapshot removing only56 entries; and checks exact after-state plus effective denial before commit. Rollback05 remains separately guarded against the saved original ACL digest and requires its own explicit RESTORE action.

Before deciding execution approval, the connected reviewer must also check the remaining runtime prerequisites in the **already saved02 output**, rather than infer them from this abbreviated summary: PostgreSQL17+, trusted postgres/no simulated JWT context, client can_login=false, no owner inheritance and no additional PUBLIC/delegated grant paths. If absent/stale/changed, stop for targeted review; do not bypass a guard. This update does not certify PostgreSQL syntax/runtime/dependency behaviour: prior preparation was static/Python-model validation only, with no SQL execution. Any desired runtime rehearsal needs its own authorisation.

The original baseline omits the target non-row table ACLs, so it can remain10fa... after correction. The new ACL fingerprint is the separate state anchor. A changed state must be re-reviewed; never replace a saved hash merely to force correction or rollback through.

## Unresolved PostgREST watcher requirement

Both are Supabase-admin-owned, SECURITY INVOKER event-trigger functions in extensions with fixed empty search paths, enabled according to earlier supplied metadata:

- extensions.pgrst_ddl_watch(): raw-body CRLF-normalized digest `de987df746eb39647098459e7993bd8595e592969b0cd647828a3d13d37cffe0`.
- extensions.pgrst_drop_watch(): corresponding digest `791b41f0632fc86e0fc86a303ec0fd710c4e2ecf947a23422dae2b7a2c122f1d`.

The owner/operator has now opened both existing definitions with the approved read-only query. They report `NOTIFY pgrst, 'reload schema';` on line26 of ddl_watch and line24 of drop_watch, no occurrences of http/webhook/email/EXECUTE/PERFORM, and unchanged recorded fingerprints. This is positive, **limited manual source-inspection evidence**, not a complete independent source/provider comparison. Full bodies were not provided to this development agent; search method/case sensitivity and all branches/indirect calls have not been independently assessed. The expected NOTIFY is a local PostgREST cache-refresh signal, not customer email or a webhook. Full verification remains OPEN; do not label the watcher requirement passed, disable/replace/re-own a watcher or invoke it as a test.

See [WATCHER_MANUAL_INSPECTION.md](WATCHER_MANUAL_INSPECTION.md) for the precise remaining work. The definitions are already available privately to the operator, so **do not repeat the retrieval query just to reproduce evidence**. Review those saved full definitions instead.

### Private retrieval method reference — operator retrieval now completed

1. Prefer an authorised administrator viewing the **existing** two definitions in the production Supabase Dashboard database-function editor, if that editor exposes event-trigger functions. Independently confirm project arnzqizcycesukplmvuc and schema extensions. Open definitions for inspection only; do not Save, Run or invoke either function.
2. If that UI does not expose them, seek separate approval for the following tightly scoped SELECT through a trusted SQL Editor/direct read-only connection. This retrieves definitions; it does NOT call the watchers. The owner now reports using this approved query read-only. It is retained as a method reference, not an instruction to retrieve the same definitions again. This development agent has not executed it:

```sql
select
  p.oid::regprocedure::text as signature,
  pg_get_functiondef(p.oid) as definition
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'extensions'
  and p.proname in ('pgrst_ddl_watch', 'pgrst_drop_watch')
  and p.pronargs = 0
  and p.prorettype = 'pg_catalog.event_trigger'::regtype
order by p.proname;
```

3. Keep the result within the trusted administrator/private review channel. Do not send raw results through a public issue/PR/chat connector, commit them, screenshot them for sharing, or paste any embedded credentials/URLs/secrets. No new database credentials or grants should be created to perform this inspection. If fewer/more than the expected two definitions appear, stop and reconcile signatures/metadata.
4. Review the complete control flow and any referenced routines. Expected provider behaviour is event-trigger metadata inspection/filtering and a fixed PostgREST schema-cache notification (for example NOTIFY/pg_notify). Such a local database notification is not an email/webhook. Verify there are no unexpected data/permission writes, dynamic SQL, process/remote-code/network/email/payment actions. A text search alone cannot establish that; inspect indirect calls where present.
5. Where available, compare complete definitions with a trusted provider-maintained baseline appropriate to the deployed Supabase/PostgREST version. Do not assume an arbitrary latest online snippet is identical or copy it over production. Have an authorised reviewer document only the project, exact signatures/body fingerprints, review method, trusted reference/version if used, conclusion and remaining caveats. Derive/compare fingerprints with the same CRLF-normalized prosrc algorithm used by02, not a different full-definition/whitespace-trimmed hash.

If body provenance/behaviour cannot be established, retain the OPEN requirement and withhold execution approval. Do not “fix” or bypass provider watchers to remove the uncertainty.

## Next decision and later sequence

The next action is **a focused private whole-body review of the already retrieved watcher definitions and independent inspection of the saved02 snapshot**, not another functional test, permission change or blind re-run of passed preflights. Once those gates are satisfied, seek separate approval for the exact unchanged03 and specific project/state. Only that future approval may authorise filling its four parameter literals. This publication is not that approval, and no SQL03/05 execution is authorised here.

After a later approved03 transaction, approved read-only04 should confirm all56 excess effective privileges denied, CRUD/other ACLs unchanged and the expected new ACL snapshot while preserving the original baseline. Keep the original full02 snapshot/digest for any separately approved rollback05; do not automatically restore excessive privileges or clean up evidence.003/004 backend installation, delivery setup, Stripe, frontend release and other outstanding launch decisions remain separate.
