-- URBANFOLD V1 REVIEW PROPOSAL ONLY — DO NOT RUN ON LIVE DATABASE YET.
-- Target: Urbanfold-Survey (live); prepared 23 Nov 2026.
-- Goal: authenticated business admin may SELECT customer surveys/photos for export,
-- but may NOT INSERT/UPDATE/DELETE another customer's survey data or private files.
-- Confirmed: one email-verified live Auth user for urbanfolduk@gmail.com.
-- Existing table/storage policy definitions were read on 23 Nov 2026.
--
-- DEPLOYMENT HOLD: explicit owner approval plus isolated A/B/admin policy tests.
-- Existing policies are permissive by default; removing admin WRITE from each
-- permissive ALL/INSERT/UPDATE policy is essential. A SELECT-only policy by itself
-- would NOT remove existing administrator WRITE permissions.
--
-- Review and test exact rollout against fresh pg_policies snapshot before applying.
-- No database mutation occurred when this file was drafted.
BEGIN;

-- Property owner retains read/write of own records, while the administrator may read.
ALTER POLICY urbanfold_properties_select ON public.properties TO authenticated
  USING ((user_id = (SELECT auth.uid()))
    OR ((SELECT auth.jwt()) ->> 'email') = 'urbanfolduk@gmail.com');
ALTER POLICY urbanfold_properties_insert ON public.properties TO authenticated
  WITH CHECK (user_id = (SELECT auth.uid()));
ALTER POLICY urbanfold_properties_update ON public.properties TO authenticated
  USING (user_id = (SELECT auth.uid()))
  WITH CHECK (user_id = (SELECT auth.uid()));

-- Child-table ALL policies stay for owners only.
-- Each explicit admin SELECT applies solely to authenticated business admin.
ALTER POLICY urbanfold_manage ON public.extensions TO authenticated
  USING (EXISTS (SELECT 1 FROM public.properties p
    WHERE p.id = extensions.property_id AND p.user_id = (SELECT auth.uid())))
  WITH CHECK (EXISTS (SELECT 1 FROM public.properties p
    WHERE p.id = extensions.property_id AND p.user_id = (SELECT auth.uid())));
CREATE POLICY urbanfold_v1_admin_select ON public.extensions FOR SELECT TO authenticated
  USING (((SELECT auth.jwt()) ->> 'email') = 'urbanfolduk@gmail.com');

ALTER POLICY urbanfold_manage ON public.rooms TO authenticated
  USING (EXISTS (SELECT 1 FROM public.properties p
    WHERE p.id = rooms.property_id AND p.user_id = (SELECT auth.uid())))
  WITH CHECK (EXISTS (SELECT 1 FROM public.properties p
    WHERE p.id = rooms.property_id AND p.user_id = (SELECT auth.uid())));
CREATE POLICY urbanfold_v1_admin_select ON public.rooms FOR SELECT TO authenticated
  USING (((SELECT auth.jwt()) ->> 'email') = 'urbanfolduk@gmail.com');

ALTER POLICY urbanfold_manage ON public.exterior_photos TO authenticated
  USING (EXISTS (SELECT 1 FROM public.properties p
    WHERE p.id = exterior_photos.property_id AND p.user_id = (SELECT auth.uid())))
  WITH CHECK (EXISTS (SELECT 1 FROM public.properties p
    WHERE p.id = exterior_photos.property_id AND p.user_id = (SELECT auth.uid())));
CREATE POLICY urbanfold_v1_admin_select ON public.exterior_photos FOR SELECT TO authenticated
  USING (((SELECT auth.jwt()) ->> 'email') = 'urbanfolduk@gmail.com');

ALTER POLICY urbanfold_manage ON public.extension_photos TO authenticated
  USING (EXISTS (SELECT 1 FROM public.properties p
    WHERE p.id = extension_photos.property_id AND p.user_id = (SELECT auth.uid())))
  WITH CHECK (EXISTS (SELECT 1 FROM public.properties p
    WHERE p.id = extension_photos.property_id AND p.user_id = (SELECT auth.uid())));
CREATE POLICY urbanfold_v1_admin_select ON public.extension_photos FOR SELECT TO authenticated
  USING (((SELECT auth.jwt()) ->> 'email') = 'urbanfolduk@gmail.com');

ALTER POLICY urbanfold_manage ON public.sketch_photos TO authenticated
  USING (EXISTS (SELECT 1 FROM public.properties p
    WHERE p.id = sketch_photos.property_id AND p.user_id = (SELECT auth.uid())))
  WITH CHECK (EXISTS (SELECT 1 FROM public.properties p
    WHERE p.id = sketch_photos.property_id AND p.user_id = (SELECT auth.uid())));
CREATE POLICY urbanfold_v1_admin_select ON public.sketch_photos FOR SELECT TO authenticated
  USING (((SELECT auth.jwt()) ->> 'email') = 'urbanfolduk@gmail.com');

ALTER POLICY urbanfold_manage ON public.room_photos TO authenticated
  USING (EXISTS (SELECT 1 FROM public.rooms r JOIN public.properties p
    ON p.id = r.property_id
    WHERE r.id = room_photos.room_id AND p.user_id = (SELECT auth.uid())))
  WITH CHECK (EXISTS (SELECT 1 FROM public.rooms r JOIN public.properties p
    ON p.id = r.property_id
    WHERE r.id = room_photos.room_id AND p.user_id = (SELECT auth.uid())));
CREATE POLICY urbanfold_v1_admin_select ON public.room_photos FOR SELECT TO authenticated
  USING (((SELECT auth.jwt()) ->> 'email') = 'urbanfolduk@gmail.com');

-- Private photo file reads: owner or admin; uploads: owner only.
-- These two existing storage policies remain bucket-limited.
ALTER POLICY urbanfold_storage_select ON storage.objects TO authenticated
  USING (
    bucket_id IN ('exterior-photos','sketch-photos','room-photos')
    AND EXISTS (
      SELECT 1 FROM public.properties p
      WHERE p.id::text = (storage.foldername(name))[1]
        AND (p.user_id = (SELECT auth.uid())
             OR ((SELECT auth.jwt()) ->> 'email') = 'urbanfolduk@gmail.com')
    )
  );

ALTER POLICY urbanfold_storage_insert ON storage.objects TO authenticated
  WITH CHECK (
    bucket_id IN ('exterior-photos','sketch-photos','room-photos')
    AND EXISTS (
      SELECT 1 FROM public.properties p
      WHERE p.id::text = (storage.foldername(name))[1]
        AND p.user_id = (SELECT auth.uid())
    )
  );
COMMIT;

-- Mandatory acceptance checks before production application:
-- A: authenticated owner can read, create, and edit their own surveys/photos.
-- B: second customer cannot read, edit, or upload to A's survey/photos.
-- C: administrator may read any customer's surveys/photos and export PDF/ZIP,
--    but cannot insert/update/delete their records or upload another user's photos.
-- D: anonymous access denied.
-- E: photo signed URLs remain temporary and private; no anon Storage read.
-- F: inspect pg_policies for other permissive policies, grants, RPCs, and storage
--    UPDATE/DELETE paths before declaring admin write access fully prohibited.
-- G: staging fixtures and admin email subject must be rechecked against production
--    before approval. Test rollback explicitly. Do not test destructive cases on
--    genuine customer records.
