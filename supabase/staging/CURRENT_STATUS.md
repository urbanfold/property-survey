# Isolated staging status — recorded 4 November 2026

## Known target and evidence

- Staging: **Urbanfold-Survey-Staging**, reference **`hexhtduvqzleoazusskh`**.
- Dashboard: https://supabase.com/dashboard/project/hexhtduvqzleoazusskh . This is the owner-supplied staging identity, not an independent project API inspection.
- Original production reference: `arnzqizcycesukplmvuc`. Never use it for these tests, seed scripts or staging client configuration.
- The owner approved staging setup and supplied screenshots of successful `setup.sql` completion and **12/12 true** `verify_readonly.sql` results. The schema is already installed on that evidence; the fresh-project installer is not the next step.
- Those metadata checks establish reported configuration results, not end-to-end real Auth/RLS/Storage isolation, exact production schema parity or F02 delivery.
- No staging connection to GitHub has been reported; none was added by the assistant. No function deployment, staging sender configuration, test receiver, dummy identities, dummy-data inserts or paid credit tests have been confirmed to the assistant.

## Complete reviewed database sequence

The exact table/column/FK/index/constraint inventory is `SCHEMA_INVENTORY.md`; authoritative source text is in the following files:

1. `000_fresh_baseline.sql`: seven original tables — properties, extensions, rooms, exterior_photos, extension_photos, sketch_photos, room_photos — explicit grants, enabled RLS, supporting nonunique indexes and three private buckets.
2. `../001_secure_access.sql`: owner/admin row policies and private object-prefix SELECT/INSERT policies, plus properties.last_submitted_at.
3. `../002_survey_purchases.sql`: survey_free_allocations, survey_credit_purchases, survey_credit_revocations; unchanged 600-pence/GBP rules and free-credit/address-lock triggers/helpers, plus address_locked.
4. `../003_survey_notifications.sql`: survey_notification_events and service-only claim/completion helpers. Does not deploy the Edge Function or configure secrets.

Together: **11 public application tables**, **7 SECURITY DEFINER helpers with fixed search paths**, **2 property triggers**, and **3 private buckets**. Bucket names are exterior-photos, sketch-photos and room-photos; extension-location photographs share exterior-photos. Object keys begin with the property UUID, including room photographs. Owners may access only their own parent/child rows/objects, apart from the existing signed admin-email exemption. The original survey tables have no anonymous app grants; notification events/service helpers are not browser-accessible. Storage bytes are uploaded through its API, never direct SQL inserts.

No migration/DDL/runtime change is proposed by this status update. £6 app credits remain separate from £179 Essential Feasibility. Test-mode Stripe purchases must not unlock live credits; no production Stripe or email credentials are needed. F02 still requires `request-survey-notification` deployment and staging-only SUPABASE variables, APP_URL and a new test-only SURVEY_NOTIFICATION_WEBHOOK_URL as detailed in README.

## First staging step for review — no SQL execution

**Reuse and inspect the existing staging project, not the fresh installer.**

1. Open the staging Dashboard link above; verify project name/reference before navigating further. Do not use a saved production SQL Editor tab.
2. In **Table Editor**, inspect that the 11 named application tables exist; do not add/edit rows. In **Storage**, inspect that the three named buckets are private; do not upload production photos or change policies.
3. Review `SCHEMA_INVENTORY.md` against the supplied 12-check screenshot. Earlier checks did not establish every FK/delete action/index/function body or production parity. Any further metadata SQL is a separately reviewed next step, not something run by this update.
4. Determine whether the two previously requested staging-only dummy Auth accounts already exist before creating duplicates. Their UUIDs have not been supplied. No passwords/API keys should be sent in chat. A new test-only client must point to staging; the current live Pages app points to production and must not be used for staging tests.

This first step performs no SQL, imports, migrations, user creation, function deployment, GitHub push/merge or application publication. Do not rerun setup.sql/000 or reset/drop anything.

## Remaining gates

- User-reviewed exact production metadata (optional read-only approval) before claiming parity: columns/defaults, FK actions, constraints/indexes, effective/default grants, RLS/policies, helper signatures/owners/settings/definitions, triggers and bucket limits/ACLs.
- New/confirmed dummy Auth A and B, with staging-only confirmation strategy; admin test identity needs an explicit decision because the application/source policies retain a fixed existing admin email. Do not copy a real Auth user.
- An isolated staging client origin and staging public anon key setup, with network inspection proving no production calls; never a service-role key in the client.
- Real dummy-owner cross-account read/write/photo signing/upload denial tests, cloud recovery/F01/exports/Leica checks, and separate notification/backend checks after approved deployment.
- A new dummy notification receiver and staging-only sender/test inbox configuration if testing real email delivery. Production Brevo credentials/settings are not staging configuration and must not be copied.
- No production writes, merges, deployment, secret rotation or live Stripe changes are authorised by resuming staging preparation. This documentation update is local only.
