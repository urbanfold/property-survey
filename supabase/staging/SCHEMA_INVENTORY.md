# Reconstructed staging schema and source/production comparison

**Source:** application/development branch after `2ea131a`, root migrations 001–003, and `tests/database_fixture.sql`. **Production evidence:** the owner's historical diagnostic of columns, policies and bucket settings (22 October context), not a current database inspection. This inventory specifies the proposed staging schema exactly; it is not a certification of current production parity.

## Original survey tables (baseline 000)

All table names below are in `public`. Unless explicitly marked NOT NULL, columns remain nullable, including ownership/FK columns, matching the historical column output. No new enums, positive-number checks, address uniqueness or room-name uniqueness are imposed. All `id` columns below are UUID primary keys, default `gen_random_uuid()`, implicitly NOT NULL. All `created_at` columns are nullable timestamptz default `now()`. Foreign keys are the fixture reconstruction, not established by the historical columns-only diagnostic; baseline FK actions are NO ACTION, non-deferrable.

| Table | Remaining columns, defaults and references |
| --- | --- |
| `properties` | `user_id uuid → auth.users(id)`; `surveyor_name text`; `address text NOT NULL`; `postcode text NOT NULL`; `property_type text`; `notes text`; `status text DEFAULT 'in_progress'`; `created_at`; `client_email text`. Migration 001 adds nullable `last_submitted_at timestamptz`; 002 adds `address_locked boolean NOT NULL DEFAULT false`. |
| `extensions` | `property_id uuid → properties(id)`; `extension_types jsonb`; `description text`; `width numeric`; `length numeric`; `created_at`. |
| `rooms` | `property_id uuid → properties(id)`; `room_name text NOT NULL`; `shape text`; `dimensions jsonb`; `additional_measurements text`; `created_at`. |
| `exterior_photos` | `property_id uuid → properties(id)`; `elevation_type text NOT NULL`; `photo_url text NOT NULL`; `created_at`. |
| `extension_photos` | `property_id uuid → properties(id)`; `photo_url text NOT NULL`; `created_at`. |
| `sketch_photos` | `property_id uuid → properties(id)`; `photo_url text NOT NULL`; `created_at`. |
| `room_photos` | `room_id uuid → rooms(id)`; `photo_url text NOT NULL`; `created_at`. |

The original seven tables therefore have seven PK indexes and seven FK constraints, including `properties.user_id`. Neither rooms nor extensions have a unique property/name constraint: the client orders by `created_at,id` and selects the latest matching record. Do not add uniqueness without data/schema review.

Client data contracts: extension type values `Front`, `Rear`, `Side`, `Single`, `Double`, `Loft Conversion` are JSON string-array entries; property types are application select values, not a database enum. Rectangular room `dimensions` uses `l,w,h`; L-shaped uses `l1,w1,l2,w2,l3,w3,h`. Values are normally strings from metre inputs, not SQL columns. Notes/additional measurements remain text. Room names include Porch, Hallway, Living Room, Kitchen, Conservatory, Landing, Bedrooms 1–4, Bathrooms 1–2, Ensuite, Loft Room and Other. This list is UI data, not lookup tables. Telephone/newsletter fields are Auth user metadata, not missing survey-table columns.

### Proposed staging-only nonunique indexes

000 adds `urbanfold_properties_owner_created(user_id,created_at,id)` and one parent/time/index per child: `urbanfold_extensions_property_created`, `urbanfold_rooms_property_created`, `urbanfold_exterior_property_created`, `urbanfold_extension_photos_property_created`, `urbanfold_sketch_property_created` on `(property_id,created_at,id)` and `urbanfold_room_photos_room_created(room_id,created_at,id)`. These seven indexes support current access paths without changing allowed data. Their existence/names in production are **unverified**; they are not new production changes.

## £6 ledger (migration 002, unchanged)

| Table | Exact column/constraint contract |
| --- | --- |
| `survey_free_allocations` | `user_id uuid PRIMARY KEY → auth.users(id) ON DELETE CASCADE`; `property_id uuid NOT NULL UNIQUE`; `allocated_at timestamptz NOT NULL DEFAULT now()`. Property UUID intentionally has **no property FK**. |
| `survey_credit_revocations` | `payment_intent_id text PRIMARY KEY`; `reason text NOT NULL`; `recorded_at timestamptz NOT NULL DEFAULT now()`. No purchase FK, allowing a revocation to precede a purchase event. |
| `survey_credit_purchases` | `checkout_session_id text PRIMARY KEY`; `payment_intent_id text NOT NULL UNIQUE`; `user_id uuid NOT NULL → auth.users(id) ON DELETE CASCADE`; `amount_total integer NOT NULL CHECK (=600)`; `currency text NOT NULL CHECK (='gbp')`; `live_mode boolean NOT NULL`; `purchased_at timestamptz NOT NULL DEFAULT now()`; `redeemed_property_id uuid UNIQUE` nullable; `redeemed_at timestamptz` nullable. Redeemed property UUID intentionally has **no property FK**. |

Ledger PK/UNIQUE constraints supply six automatic indexes across these three tables (2 allocations, 1 revocations, 3 purchases). No extra ledger indexes are introduced. Allocation/redemption UUIDs survive property deletion so deletion cannot replenish credits. First ordinary-account property consumes a lifetime free allocation; further properties require an unspent, non-revoked **live-mode** £6 credit. Existing rows are grandfathered by the migration backfill. Admin/privileged maintenance is exempt. Address lock engages on submission; measurements remain editable. Price/entitlement rules are not changed for staging. A browser payment-return query never creates a credit. £179 Essential Feasibility is not a table, price, credit or product in this setup.

## F02 event ledger (migration 003, unchanged)

`survey_notification_events`: `id uuid PRIMARY KEY DEFAULT gen_random_uuid()`; `property_id uuid NOT NULL → properties(id) ON DELETE CASCADE`; `actor_id uuid NOT NULL → auth.users(id) ON DELETE CASCADE`; `submission_at timestamptz NOT NULL`; `content_fingerprint text NOT NULL CHECK (64 lower-case hex characters)`; `state text NOT NULL DEFAULT 'sending' CHECK IN ('sending','accepted','uncertain')`; `created_at timestamptz NOT NULL DEFAULT now()`; `finished_at timestamptz` nullable. Unique `(property_id,submission_at)` and `(property_id,content_fingerprint)`. PK and two UNIQUE indexes plus `survey_notification_actor_time(actor_id,created_at)`.

No caller-facing event policy: direct anonymous/authenticated access revoked. Event claim checks the actual confirmed Auth actor and owner/admin, current `last_submitted_at`, saved recipient and unchanged-content hash. Claims serialize actor limits with an advisory transaction lock and the property row. Limits remain proposed 20/account and 5/property/rolling 24h. Uncertain delivery is not blindly retried. The function reads child tables but does not create a transaction around all client survey saves; concurrent edits/retention remain audit concerns.

## RLS, ACLs, helpers and triggers

RLS enabled on all 11 public tables. RLS is not FORCE RLS; service_role retains Supabase's intentional server-only bypass. No Auth/Storage roles/tables/functions are recreated.

| Object | Effective intended caller access |
| --- | --- |
| `properties` | authenticated SELECT/INSERT/UPDATE only; owner or signed admin email `urbanfolduk@gmail.com`; no client DELETE policy/grant. |
| Six survey child tables | authenticated SELECT/INSERT/UPDATE/DELETE; parent property owner/admin, room photos through rooms→properties. `USING` and `WITH CHECK` both constrain mutations. |
| Free allocations, purchases | authenticated SELECT own/admin only; no client mutation; service_role ALL. |
| Revocations | service_role only, no client policy or grant. |
| Notification events | service_role only, no client policy or grant. |
| Original survey tables | service_role ALL; anonymous/PUBLIC app table privileges explicitly revoked by 000. |
| `storage.objects` | existing managed ACLs; policy SELECT/INSERT only in the three buckets and property-ID prefix belonging to owner/admin. No app UPDATE/DELETE policies. |

001 defines exactly `urbanfold_properties_select`, `_insert`, `_update`; one `urbanfold_manage` ALL policy per child; and `urbanfold_storage_select`, `_insert`. 002 adds `urbanfold_free_read` and `urbanfold_purchase_read`. 001 aborts on unknown additional policies and missing/public buckets; do not weaken that check. Existing broad policies from the historical diagnostics are removed only by their known names.

All seven custom public functions are SECURITY DEFINER with fixed empty search_path and qualified application references. Their full authoritative definitions are in 002/003, included byte-for-byte in the generated setup bundle:

| Function signature → result | Execution / purpose |
| --- | --- |
| `get_survey_allowance() → jsonb` | authenticated only; requires auth.uid; returns free/paid/admin allowance, 600 pence, GBP. |
| `enforce_survey_allowance() → trigger` | direct PUBLIC/anon/authenticated EXECUTE revoked; BEFORE INSERT `urbanfold_survey_allowance` on properties; serializes via Auth user lock, allocates/redeems. |
| `protect_survey_address() → trigger` | direct PUBLIC/anon/authenticated EXECUTE revoked; BEFORE UPDATE `urbanfold_protect_address` on properties; non-admin submitted address/postcode lock. |
| `record_survey_purchase(text,text,uuid,integer,text,boolean) → void` | service_role only; validates IDs, amount/currency/mode, idempotent purchase recording. |
| `revoke_survey_purchase(text,text) → void` | service_role only; idempotent revocation by payment intent. |
| `claim_survey_notification(uuid,uuid,timestamptz) → jsonb` | service_role only; confirmed actor/owner/revision validation, deduplication and caps. |
| `finish_survey_notification(uuid,boolean) → void` | service_role only; transitions sending to accepted/uncertain. |

Supabase provides `auth.uid()`, `auth.jwt()`, `storage.foldername(text)`, Auth identities/users and Storage services. PostgreSQL provides `gen_random_uuid`, SHA-256/byte conversions, JSON and advisory locks; no custom extension is created by the baseline. The exact live SECURITY DEFINER warning for get_survey_allowance remains unverified: a staging definition does not resolve or validate a different deployed definition.

## Private photograph storage

Buckets: `exterior-photos`, `sketch-photos`, `room-photos`, all `public=false`. Extension-location photos share exterior-photos; there is no extension-only bucket. Current client compresses images to JPEG and uploads `<property UUID>/<random UUID>.jpg`, including room photos (prefix is property ID, not room ID). Rows store `storage://<bucket>/<path>`; legacy same-project URL forms are supported by the client. Signed display URLs last one hour and are cached for about 55 minutes.

Only bucket configuration is inserted through SQL; use the Storage API for actual file bytes/metadata. No direct `storage.objects` inserts are allowed in the staging guide. Deleting a photo in the app deletes its database reference, retaining the private bytes; a reviewed orphan-retention process is still needed. New uploads use fresh names, so overwrite/update policy is unnecessary.

Limits remain NULL in the reconstruction, matching the historical bucket output. Server MIME/size hardening remains open F06; it is not silently imposed as a compatibility change. Private bucket does not mean a copied unexpired signed URL cannot be used by its bearer. RLS prevents B from generating links for A; issued links are not per-request account sessions.

## Fixture versus production evidence / staging differences

| Area | Fixture | Actual evidence / proposed staging |
| --- | --- | --- |
| Original columns | Models earlier diagnostic | Same observed names/types/nullability/defaults; current production additions/drift unverified. |
| PK/FK actions | Assumed PKs/FKs, default NO ACTION | Not present in earlier column output; baseline follows fixture pending metadata. |
| Auth | Fake roles, `auth.users(id)` and setting-based JWT helper | Real Supabase-managed Auth; F02 reads email/confirmation. Notification test adds email columns locally, not an Auth migration. |
| Storage | Fake buckets(id,public), objects(id,bucket_id,name), folder helper | Real Storage has name, owner/metadata/object and service semantics. Baseline only inserts private buckets and relies on managed ACLs; real API still needs testing. |
| Grants | Broad CRUD to anon/authenticated across all fixture tables; tests may see zero rows via RLS | Baseline explicitly denies anonymous app tables and grants minimum client operations; permission-denied can replace fixture's zero-row result. This fixes the missing original-table GRANT problem on new projects. |
| Legacy policies | Small representative broad-policy subset | Earlier actual diagnostic included more duplicates/child policies; 001 lists their names. Fresh staging has none; current production policy set still needs metadata. |
| Indexes/constraints | Only constraint-created indexes | Staging adds seven nonunique parent/time indexes; not proof of deployed indexes. No new room/address uniqueness. |
| Functions/triggers | 001/002/003 installed by isolated tests | Current production function bodies, ownership, ACLs and enabled triggers have not been fetched. F02 is a candidate, not known installed live. |
| Payment tests | Inject synthetic users/ledger/claims as privileged local test SQL | Never run fixtures in Supabase. Real Stripe sandbox payments still cannot unlock live credits; optional separate dummy-only synthetic ledger seed tests unchanged redemption without altering the rule. |
| Schemas/default privileges | Simplified and broad in fixture | Real Supabase Data API exposure, role ACL/default ACL, version, owner and managed Storage access must be checked. |

Open F04 remains: photo-reference rows are owner-controlled, but no constraint proves a stored URL/path belongs to that row's property. A user may insert a bad reference; Storage still must deny the other owner's object. The baseline does not silently close this finding by inventing untested URL constraints. Admin relies on the existing signed email identity without an aal2 condition; changing that role model is also outside this baseline.

## Required production metadata before claiming parity

With separate approval, run only `metadata_readonly.sql` against production and review its output privately: all columns/defaults/nullability; PK/FK/UNIQUE/CHECK definitions and delete actions; indexes; RLS and FORCE flags; policy names/roles/commands/expressions; effective/default table/function privileges; both property triggers and extra triggers; all helper signatures/owners/fixed search paths/body fingerprints; bucket privacy/limits and managed Storage ACLs. Independently inspect unfamiliar function/trigger/view definitions for hidden dependencies without copying secrets into chat/repo. Fingerprints alone cannot explain changed logic; exact reviewed definitions may be necessary in a secure channel.

Also verify current deployed Edge Function versions/configuration and API-exposed schemas separately. Do not infer their state from checked-in source. No production rows, Auth users, passwords, files or secret values are needed for this metadata comparison. Until that comparison and isolated real-service tests pass, call this a **source-compatible staging reconstruction**, not an exact production clone.
