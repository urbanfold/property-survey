# Read-only production reconciliation — 7 November 2026

**Decision: preserve production schema/services and HOLD installation approval pending the focused checks below.** Only installer type acceptance is revised. No production query, migration, DDL, function deployment, notification, secret/configuration change, payment, merge or cleanup was executed. Canonical source remains5d434a78ac1f997c86b9c92646771de2018cad04; original reviewed package isd42263a8fb10e44136564a5224c956bcc47c89c7. This report/guard change is to be committed locally to the development branch only, not pushed under this instruction.

## Evidence boundary

The owner supplied preflight findings and the actual trigger/default-ACL/definer/dependency sections in chat. They are recorded as **owner-supplied**, not independent database access by this agent, under audits/2026-11-07/production-reconciliation. Observed baseline:

`10fa3ce6272648b31c662735e549b2e78b032a63cceb6e5f1d862f5d5052e4f6`

The complete underlying metadata JSON (columns/constraints/index definitions/effective grants and other fields) was not provided, so this agent cannot independently recompute that digest. It remains OBSERVED, NOT APPROVED. Installer settings retain NOT_APPROVED / REVIEW_REQUIRED; the reported digest is not prefilled. The original00 SQL and its baseline expression are byte-for-byte unchanged (SHA256 faada72c6159ca4b701a936b7bf1ecb21758fc7fd3c4bbdf592f0f6172e12c16).

## Reconciliation decisions

| Finding | Assessment / exact recommendation |
|---|---|
| Production extensions.width/length numeric(5,2); model numeric | **Compatible existing precision constraint; guard false negative.**001/002 do not create/retype these original extension columns.003 reads whole saved extension rows into a fingerprint;004 does not use them. Existing inputs use metres/step0.01. Keep production types. Revise ONLY10/20's required-column predicate to accept exact numeric(5,2) in addition to numeric for these TWO fields. Every other type/table/column remains exact; no generic numeric typmod acceptance. |
| Seven production FKs have ON DELETE CASCADE; model lacks that action | **Existing lifecycle behaviour, not a003/004 prerequisite mismatch.**001 does not define those legacy FKs;002's own new Auth FKs already explicitly cascade. Do not replace production FKs to match a simplified test fixture.003/004 do not delete existing accounts/properties/children or alter these FKs. The supplied summary gives seven, not their exact mappings; inspect the existing full constraints or supplemental01 before signing off each mapping/validation. Auth/property deletion can already cascade metadata, and does not imply automatic removal of Storage bytes. Existing credit allocation/redemption property UUIDs deliberately have no property FK; do not add a cascade/reset there. |
| Thirteen policies match;13 indexes present/valid; buckets private | **Owner-confirmed positive evidence.** Preserve them. Presence/count alone is not an index/constraint definition proof; confirm actual uniqueness and FK mapping against002. The new installer still requires exact policy equality and unchanged reviewed baseline. No001 replay or policy replacement proposed. |
| Seven legacy survey/photo tables have anonymous SQL grants | **CRUD grants alone are compatible with deny-by-default RLS.** The existing isolated fixture also grants these CRUD privileges;001 tightens policies rather than blanket-revoking legacy table grants. With the reported RLS and exact authenticated-only policies, those grants do not themselves permit anonymous row access. BUT RLS is not protection for TRUNCATE/REFERENCES; broad non-row privileges require the separate check below. No blanket revocation or declaration that all grants are harmless. |
| Default ACLs grant broad public-schema rights to anon/authenticated | **Recognised broad provider/project defaults; preserve global defaults.** The supplied postgres/public table ACL includes arwdDxtm (including TRUNCATE/REFERENCES/TRIGGER/MAINTAIN), function defaults include EXECUTE, sequences include read/write/usage. Supabase-admin defaults across managed schemas and Auth/Realtime roles must not be rewritten to fix these four new objects. Defaults are future-object rules, not proof of actual existing table grants.003/004 explicitly revoke PUBLIC/anon/authenticated rights before granting narrow intended access; inside-transaction checks reject effective unexpected client access, including inherited rights. Supplied client_memberships=[] reduces inherited-client-role ambiguity, but is not proof of role bypass/ownership attributes. |

`numeric(5,2)` accepts up to three integer digits/two fractional digits (ordinary finite range -999.99 to999.99), rounds extra fractional precision and rejects overflow. This is an existing schema limitation, not caused by notifications. No widening/rounding/data rewrite is proposed. Room dimensions stored in JSON are unaffected. The source model stays truthful about its unconstrained numeric fixture; accepted exceptions are separately documented rather than rewriting that model as though it were production metadata.

## Existing function/trigger/dependency inspection

- Five supplied public SECURITY DEFINER entries have owner postgres, fixed empty search_path, no anonymous EXECUTE; authenticated EXECUTE only for get_survey_allowance. Purchase/revocation and trigger helper grants are postgres/service_role. This is the intended restricted design; do not revoke the allowance RPC from customers.
- Supplied raw body digests for get_survey_allowance, enforce_survey_allowance, protect_survey_address and record_survey_purchase exactly match the pinned source bodies INCLUDING outer whitespace. The normalized comparison separately reported by the owner says all five match.
- **Transcription issue RESOLVED:** the original pasted revoke_survey_purchase raw digest had61 characters. The owner then reconfirmed live production read-only: full raw digest `c7e24897638c74ca7f9815c43091b86b0433bdad77284f8b79dc8e3b9ce45380`, normalized digest `09d97cbf0f492925affe2eca085eebdbaa12863269c6f7751be957678b77d433`, normalized source match=true. Both corrected digests match canonical source. All FIVE raw bodies now reconcile against supplied evidence; no replacement or additional dedicated revocation-function test is needed. The original typo and subsequent correction are both retained with their provenance.
- Exactly two supplied properties triggers are enabled O. Both trigger definition hashes match the canonical PostgreSQL definitions:
  - urbanfold_survey_allowance: BEFORE INSERT, FOR EACH ROW, enforce_survey_allowance().
  - urbanfold_protect_address: BEFORE UPDATE, FOR EACH ROW, protect_survey_address().
  Their raw bodies also match. Dependencies list only their expected property triggers; the other three billing helpers have no catalog dependents, and all five have no extension membership. Catalog dependency lists do not find every dynamic application invocation.
- **public.rls_auto_enable is absent from the supplied complete public-function dependency inventory**, whose original00 filter includes that name regardless of SECURITY DEFINER, and from the supplied definer/event-trigger inventories. No production automatic-RLS ACL correction is warranted from a staging warning.01 explicitly returns its current presence/type/ACL to confirm the inventory, not to change it.
- Six enabled DDL event triggers are supplied, all supabase_admin-owned, SECURITY INVOKER, fixed empty path. Four are extension-scoped: issue_graphql_placeholder (DROP EXTENSION), issue_pg_cron_access, issue_pg_graphql_access and issue_pg_net_access (CREATE EXTENSION).003/004 install no extensions, so these tagged handlers are not activated by their commands.
- pgrst_ddl_watch and pgrst_drop_watch have unfiltered tags and can run on applicable DDL. Their names/ownership/settings are consistent with normal Supabase/PostgREST maintenance watchers; no custom Urbanfold Auth/DDL notification hook is shown. **Their actual bodies were not supplied and their hashes alone do not prove absence of network/other side effects.** The connected reviewer should validate these provider-owned watcher definitions privately against the deployed provider baseline before installation approval. Do not alter/disable provider watchers.01 returns namespace/hash and a conservative network-name flag, not raw definitions/secrets; that flag cannot prove safety or identify all dynamic calls.

There is no demonstrated production schema/business-function correction from the supplied differences. The only confirmed installer compatibility problem is the overly exact two-column numeric check. Unknown grants/body metadata are review gaps, not permission to change working services.

## Narrow guard diff and preserved safeguards

Only scripts/build_production_backend_review.py and the generated10/20 predicate change executable logic. The exception is precisely:

- required table=extensions;
- required column=width or length;
- reference type=numeric;
- actual type=numeric(5,2).

Original exact type equality remains available. numeric(6,2), numeric(5,3), numeric(5,1), integer, float, text, a different table/column or a different reference type do NOT gain acceptance. No function/policy/default-grant/FK changes, no changes to the baseline fingerprint algorithm or canonical003/004 body. Original00/30, source_spec/reference,40/41,50/51 remain byte-identical to d42263a. Role, source-body, policy, table RLS, existing trigger, fresh-object, baseline digest, approval and post-install permission guards remain. No actual production digest is automatically approved.

## Exact next safe action

**Only the separately reviewed SELECT-only `01_reconciliation_readonly.sql` is the next proposed database action; no installer yet.** The connected reviewer must independently verify project arnzqizcycesukplmvuc and review this query first. It:

1. Uses the original unchanged baseline expression and reports whether the current digest still equals the observed10fa... value. A changed digest requires renewed metadata review, not substitution of a new digest into installers.
2. Reports the current five normalized billing-body/ACL/header comparisons as metadata (no function calls; the pasted revocation-hash issue is already resolved) and explicit public.rls_auto_enable presence/ACL/extension metadata.
3. Reports effective anon/authenticated CRUD plus TRUNCATE/REFERENCES/TRIGGER, table ACL entries (including MAINTAIN where supported), role superuser/BYPASSRLS/ownership flags and exact FK delete rules. RLS does not govern all these privileges. If unnecessary non-row rights are present, prepare a separate per-table/per-role correction only after actual grants/API reachability/compatibility are understood; never blanket-revoke provider defaults or treat SQL privileges as a proven direct PostgREST exploit.
4. Expands default ACLs and DDL handler metadata for private review. It returns no customer/Auth rows, full function bodies, trigger arguments, keys or credentials; it sends nothing.

Also confirm the unfiltered pgrst watcher bodies privately with the connected reviewer; do not paste secret-bearing source. If01 confirms the same observed baseline, correct billing match/ACLs, expected FKs and safe role/non-row access, and provider watchers are understood, the reviewer can finish the comparison and seek SEPARATE approval to install the revised10 followed by20. Keep production leaked-password protection, notification provider/recipient/scheduler and existing Stripe review decisions from the README as later release gates. Do not replay001/002, create migration-history guesses, run a staging installer, change services or enable notifications during reconciliation.

## Checks performed in this change

-23 PostgreSQL SELECT-only type cases pass, including both accepted width/length shapes and rejected out-of-scope variations.
-SELECT-only numeric precision checks pass; no application table/data/type was changed.
-Supplemental catalog query was parsed/evaluated in an empty network-disabled PostgreSQL17 cluster with ONLY its app-baseline subexpression stubbed to {}. No Auth/Storage fixture, application DDL, migrations, application functions or real services were executed. This does not establish actual production grants/watchers or validate a future installation.
-Byte comparisons prove original00/30/reference/source_spec/recovery/scheduler unchanged, and10/20 differ ONLY in the scoped type predicate. Canonical001–004, application, payment handlers and workflows unchanged. Generator parity passes. Prior installation rehearsal evidence remains available, not re-executed or relabelled as a live test.

No schema rollback is needed for this review-only commit. If the guard exception needs revision, revert just this local review change; never change production numeric types/FKs/grants as a way to fit the fixture.

Current integrity inventory: SHA256SUMS.txt and audits/2026-11-07/production-reconciliation/FILE_MANIFEST.json. The prior production-backend-review manifest/logs remain historical evidence of d42263a and are not overwritten.
