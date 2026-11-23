-- REVIEW PROPOSAL ONLY. NOT APPLIED. NOT A PRODUCTION MIGRATION.
-- Urbanfold-Survey-Staging project hexhtduvqzleoazusskh.
-- Apply only after approval and an isolated owner/A/B access test.
-- Stage administrator UUID is the same independently verified subject used by
-- staging-stripe-payment-verify-readonly and staging admin review.
-- Existing RLS (owner read/write) stays intact. These policies add SELECT ONLY.
-- No service key, writable admin override, or production permission change.
--
-- Prerequisite: confirm auth.users.id and email confirmation for this exact
-- staging administrator UUID; read back RLS/storage policies before applying.
BEGIN;

CREATE POLICY urbanfold_staging_export_admin_read
  ON public.properties FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = 'b83f87d8-abf2-4800-beab-8279917804c7'::uuid);

CREATE POLICY urbanfold_staging_export_admin_read
  ON public.extensions FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = 'b83f87d8-abf2-4800-beab-8279917804c7'::uuid);

CREATE POLICY urbanfold_staging_export_admin_read
  ON public.rooms FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = 'b83f87d8-abf2-4800-beab-8279917804c7'::uuid);

CREATE POLICY urbanfold_staging_export_admin_read
  ON public.exterior_photos FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = 'b83f87d8-abf2-4800-beab-8279917804c7'::uuid);

CREATE POLICY urbanfold_staging_export_admin_read
  ON public.extension_photos FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = 'b83f87d8-abf2-4800-beab-8279917804c7'::uuid);

CREATE POLICY urbanfold_staging_export_admin_read
  ON public.sketch_photos FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = 'b83f87d8-abf2-4800-beab-8279917804c7'::uuid);

CREATE POLICY urbanfold_staging_export_admin_read
  ON public.room_photos FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = 'b83f87d8-abf2-4800-beab-8279917804c7'::uuid);

-- Private buckets only; no INSERT/UPDATE/DELETE grants.
CREATE POLICY urbanfold_staging_export_admin_read
  ON storage.objects FOR SELECT TO authenticated
  USING (
    bucket_id IN ('exterior-photos', 'sketch-photos', 'room-photos')
    AND (SELECT auth.uid()) = 'b83f87d8-abf2-4800-beab-8279917804c7'::uuid
  );

COMMIT;

-- Before approval verify under real authenticated JWTs:
-- 1) admin may SELECT another customer's survey and sign/read its private photos;
-- 2) customer A cannot SELECT customer B's data or private photos;
-- 3) anonymous cannot SELECT anyone's data or private photos;
-- 4) staging admin cannot INSERT/UPDATE/DELETE another customer's records;
-- 5) ZIP contains correct survey/room/photos and PDF renders correctly.
-- NB: UPDATE also requires SELECT, so check explicit UPDATE policies remain owner-only.
-- NB: original prod-email admin exception remains in existing staging policies;
-- review its removal separately, after confirming impact. Do not extend write privileges.
