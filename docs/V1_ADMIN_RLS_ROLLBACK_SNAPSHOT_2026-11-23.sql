-- URBANFOLD V1 — ROLLBACK DRAFT ONLY. DO NOT RUN ON LIVE.

-- Read-only source: actual live pg_policies on 23 November 2026.

-- Must re-capture and compare current live policies immediately before an approved deployment.

-- Rehearse this exact script on a schema-matched isolated database before approval.

BEGIN;

DROP POLICY IF EXISTS "urbanfold_v1_admin_select" ON "public"."extensions";

DROP POLICY IF EXISTS "urbanfold_v1_admin_select" ON "public"."rooms";

DROP POLICY IF EXISTS "urbanfold_v1_admin_select" ON "public"."exterior_photos";

DROP POLICY IF EXISTS "urbanfold_v1_admin_select" ON "public"."extension_photos";

DROP POLICY IF EXISTS "urbanfold_v1_admin_select" ON "public"."sketch_photos";

DROP POLICY IF EXISTS "urbanfold_v1_admin_select" ON "public"."room_photos";

ALTER POLICY "urbanfold_manage" ON "public"."extension_photos" TO authenticated
  USING ((EXISTS ( SELECT 1
   FROM properties p
  WHERE ((p.id = extension_photos.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> 'email'::text) = 'urbanfolduk@gmail.com'::text))))))
  WITH CHECK ((EXISTS ( SELECT 1
   FROM properties p
  WHERE ((p.id = extension_photos.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> 'email'::text) = 'urbanfolduk@gmail.com'::text))))));

ALTER POLICY "urbanfold_manage" ON "public"."extensions" TO authenticated
  USING ((EXISTS ( SELECT 1
   FROM properties p
  WHERE ((p.id = extensions.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> 'email'::text) = 'urbanfolduk@gmail.com'::text))))))
  WITH CHECK ((EXISTS ( SELECT 1
   FROM properties p
  WHERE ((p.id = extensions.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> 'email'::text) = 'urbanfolduk@gmail.com'::text))))));

ALTER POLICY "urbanfold_manage" ON "public"."exterior_photos" TO authenticated
  USING ((EXISTS ( SELECT 1
   FROM properties p
  WHERE ((p.id = exterior_photos.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> 'email'::text) = 'urbanfolduk@gmail.com'::text))))))
  WITH CHECK ((EXISTS ( SELECT 1
   FROM properties p
  WHERE ((p.id = exterior_photos.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> 'email'::text) = 'urbanfolduk@gmail.com'::text))))));

ALTER POLICY "urbanfold_properties_insert" ON "public"."properties" TO authenticated
  WITH CHECK (((user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> 'email'::text) = 'urbanfolduk@gmail.com'::text)));

ALTER POLICY "urbanfold_properties_select" ON "public"."properties" TO authenticated
  USING (((user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> 'email'::text) = 'urbanfolduk@gmail.com'::text)));

ALTER POLICY "urbanfold_properties_update" ON "public"."properties" TO authenticated
  USING (((user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> 'email'::text) = 'urbanfolduk@gmail.com'::text)))
  WITH CHECK (((user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> 'email'::text) = 'urbanfolduk@gmail.com'::text)));

ALTER POLICY "urbanfold_manage" ON "public"."room_photos" TO authenticated
  USING ((EXISTS ( SELECT 1
   FROM (rooms r
     JOIN properties p ON ((p.id = r.property_id)))
  WHERE ((r.id = room_photos.room_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> 'email'::text) = 'urbanfolduk@gmail.com'::text))))))
  WITH CHECK ((EXISTS ( SELECT 1
   FROM (rooms r
     JOIN properties p ON ((p.id = r.property_id)))
  WHERE ((r.id = room_photos.room_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> 'email'::text) = 'urbanfolduk@gmail.com'::text))))));

ALTER POLICY "urbanfold_manage" ON "public"."rooms" TO authenticated
  USING ((EXISTS ( SELECT 1
   FROM properties p
  WHERE ((p.id = rooms.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> 'email'::text) = 'urbanfolduk@gmail.com'::text))))))
  WITH CHECK ((EXISTS ( SELECT 1
   FROM properties p
  WHERE ((p.id = rooms.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> 'email'::text) = 'urbanfolduk@gmail.com'::text))))));

ALTER POLICY "urbanfold_manage" ON "public"."sketch_photos" TO authenticated
  USING ((EXISTS ( SELECT 1
   FROM properties p
  WHERE ((p.id = sketch_photos.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> 'email'::text) = 'urbanfolduk@gmail.com'::text))))))
  WITH CHECK ((EXISTS ( SELECT 1
   FROM properties p
  WHERE ((p.id = sketch_photos.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> 'email'::text) = 'urbanfolduk@gmail.com'::text))))));

ALTER POLICY "urbanfold_storage_insert" ON "storage"."objects" TO authenticated
  WITH CHECK (((bucket_id = ANY (ARRAY['exterior-photos'::text, 'sketch-photos'::text, 'room-photos'::text])) AND (EXISTS ( SELECT 1
   FROM properties p
  WHERE (((p.id)::text = (storage.foldername(objects.name))[1]) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> 'email'::text) = 'urbanfolduk@gmail.com'::text)))))));

ALTER POLICY "urbanfold_storage_select" ON "storage"."objects" TO authenticated
  USING (((bucket_id = ANY (ARRAY['exterior-photos'::text, 'sketch-photos'::text, 'room-photos'::text])) AND (EXISTS ( SELECT 1
   FROM properties p
  WHERE (((p.id)::text = (storage.foldername(objects.name))[1]) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> 'email'::text) = 'urbanfolduk@gmail.com'::text)))))));

COMMIT;

-- Post-rollback: compare full pg_policies snapshot; verify owner A/B, anonymous denial, admin exports.
