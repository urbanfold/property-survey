# PostgREST watchers: independent behavioural review completed — 7 November 2026

**Behavioural review COMPLETE on the owner-supplied independent review evidence. No authenticated upstream-version comparison was performed. SQL03 remains NOT APPROVED for execution.** This documentation update changes no functions, SQL, approval parameters or production permissions.

## Reviewed production definitions

Project: `arnzqizcycesukplmvuc`. An independent reviewer inspected the complete production definitions retrieved with the specifically authorised read-only SELECT query. This development agent records the supplied conclusion; it has not independently retrieved or executed the functions.

| Function | Recorded CRLF-normalized body SHA-256 | Complete behavioural finding |
|---|---|---|
| extensions.pgrst_ddl_watch() | de987df746eb39647098459e7993bd8595e592969b0cd647828a3d13d37cffe0 | Loops through pg_event_trigger_ddl_commands(), filters relevant DDL command tags, excludes pg_temp schema objects, then issues fixed NOTIFY pgrst, 'reload schema'. |
| extensions.pgrst_drop_watch() | 791b41f0632fc86e0fc86a303ec0fd710c4e2ecf947a23422dae2b7a2c122f1d | Loops through pg_event_trigger_dropped_objects(), filters relevant dropped object types, excludes temporary objects, then issues the same schema-cache notification. |

The reviewer examined complete control flow and function calls: no dynamic SQL, permission/data modifications, external network calls, email, payment actions or unreviewed user-defined function calls were found. Previously supplied metadata records both as enabled, supabase_admin-owned SECURITY INVOKER functions with empty search paths. The fixed NOTIFY is a local PostgREST schema-cache signal, not an external delivery.

## Evidence progression and limits

The earlier operator inspection found NOTIFY at lines26/24 and no five searched keywords. That was partial evidence only. The new independent whole-body/call-flow review supersedes the earlier OPEN behavioural gate for these retrieved definitions. Historical evidence is preserved in the prior commits; raw function definitions remain in the private review channel.

No separate authenticated upstream Supabase version comparison was performed. Therefore provider provenance/version equivalence is NOT certified. This limitation does not undo the complete behavioural conclusion for the inspected definitions. If definitions or fingerprints change, review the changed source before relying on this conclusion; do not infer unchanged behaviour from names alone. No watcher modification, disabling, re-ownership or invocation is recommended.

## SQL03 readiness

The focused behavioural gate is now closed. The isolated PostgreSQL17.11 rehearsal published in commit `8710ff81df7249b92e7c37729f4cd9d77e14f773` passed all18 checks of unchanged03/05 logic using only four documented local parameter substitutions. It did not test the actual managed watchers or connect to Supabase. See [rehearsal report](../../../../audits/2026-11-07/acl-runtime-rehearsal/README.md).

SQL03 is ready for a separate execution-approval decision subject to the saved02 guard/target review described in [PREFLIGHT02_REVIEW.md](PREFLIGHT02_REVIEW.md). No further watcher retrieval or upstream comparison is required for this focused behavioural gate. Live-state drift, connection identity and explicit approval remain separate prerequisites. Approval placeholders remain untouched. No production/staging SQL or other live operation was performed in this update.
