-- Urbanfold: owner/admin access and private photo storage.
-- Run as the project owner in Supabase SQL Editor, before deploying this release.
-- Transactional and repeatable. Does not delete or rewrite survey records or photos.
begin;

alter table public.properties add column if not exists last_submitted_at timestamptz;

drop policy if exists "Allow users to insert properties" on public.properties;
drop policy if exists "Allow users to insert their own properties" on public.properties;
drop policy if exists "Allow users to update properties" on public.properties;
drop policy if exists "Allow users to view properties" on public.properties;
drop policy if exists "Allow users to view their own properties" on public.properties;
drop policy if exists "Users can insert own properties" on public.properties;
drop policy if exists "Users can update own properties" on public.properties;
drop policy if exists "Users can view own properties" on public.properties;
drop policy if exists "Users can manage own extensions" on public.extensions;
drop policy if exists "Users can manage own rooms" on public.rooms;
drop policy if exists "Users can manage own exterior photos" on public.exterior_photos;
drop policy if exists "Users can manage own extension photos" on public.extension_photos;
drop policy if exists "Users can manage own sketches" on public.sketch_photos;
drop policy if exists "Users can manage own room photos" on public.room_photos;
drop policy if exists "Allow authenticated users to upload photos" on storage.objects;
drop policy if exists "Allow public access to view photos" on storage.objects;
drop policy if exists "Public Access for Photos" on storage.objects;

alter table public.properties enable row level security;
drop policy if exists urbanfold_properties_select on public.properties;
create policy urbanfold_properties_select on public.properties for select to authenticated using (user_id = (select auth.uid()) or ((select auth.jwt()) ->> 'email' = 'urbanfolduk@gmail.com'));
drop policy if exists urbanfold_properties_insert on public.properties;
create policy urbanfold_properties_insert on public.properties for insert to authenticated with check (user_id = (select auth.uid()) or ((select auth.jwt()) ->> 'email' = 'urbanfolduk@gmail.com'));
drop policy if exists urbanfold_properties_update on public.properties;
create policy urbanfold_properties_update on public.properties for update to authenticated using (user_id = (select auth.uid()) or ((select auth.jwt()) ->> 'email' = 'urbanfolduk@gmail.com')) with check (user_id = (select auth.uid()) or ((select auth.jwt()) ->> 'email' = 'urbanfolduk@gmail.com'));

alter table public.extensions enable row level security;
drop policy if exists urbanfold_manage on public.extensions;
create policy urbanfold_manage on public.extensions for all to authenticated
  using (exists (select 1 from public.properties p where p.id = extensions.property_id and (p.user_id = (select auth.uid()) or ((select auth.jwt()) ->> 'email' = 'urbanfolduk@gmail.com')))) with check (exists (select 1 from public.properties p where p.id = extensions.property_id and (p.user_id = (select auth.uid()) or ((select auth.jwt()) ->> 'email' = 'urbanfolduk@gmail.com'))));

alter table public.rooms enable row level security;
drop policy if exists urbanfold_manage on public.rooms;
create policy urbanfold_manage on public.rooms for all to authenticated
  using (exists (select 1 from public.properties p where p.id = rooms.property_id and (p.user_id = (select auth.uid()) or ((select auth.jwt()) ->> 'email' = 'urbanfolduk@gmail.com')))) with check (exists (select 1 from public.properties p where p.id = rooms.property_id and (p.user_id = (select auth.uid()) or ((select auth.jwt()) ->> 'email' = 'urbanfolduk@gmail.com'))));

alter table public.exterior_photos enable row level security;
drop policy if exists urbanfold_manage on public.exterior_photos;
create policy urbanfold_manage on public.exterior_photos for all to authenticated
  using (exists (select 1 from public.properties p where p.id = exterior_photos.property_id and (p.user_id = (select auth.uid()) or ((select auth.jwt()) ->> 'email' = 'urbanfolduk@gmail.com')))) with check (exists (select 1 from public.properties p where p.id = exterior_photos.property_id and (p.user_id = (select auth.uid()) or ((select auth.jwt()) ->> 'email' = 'urbanfolduk@gmail.com'))));

alter table public.extension_photos enable row level security;
drop policy if exists urbanfold_manage on public.extension_photos;
create policy urbanfold_manage on public.extension_photos for all to authenticated
  using (exists (select 1 from public.properties p where p.id = extension_photos.property_id and (p.user_id = (select auth.uid()) or ((select auth.jwt()) ->> 'email' = 'urbanfolduk@gmail.com')))) with check (exists (select 1 from public.properties p where p.id = extension_photos.property_id and (p.user_id = (select auth.uid()) or ((select auth.jwt()) ->> 'email' = 'urbanfolduk@gmail.com'))));

alter table public.sketch_photos enable row level security;
drop policy if exists urbanfold_manage on public.sketch_photos;
create policy urbanfold_manage on public.sketch_photos for all to authenticated
  using (exists (select 1 from public.properties p where p.id = sketch_photos.property_id and (p.user_id = (select auth.uid()) or ((select auth.jwt()) ->> 'email' = 'urbanfolduk@gmail.com')))) with check (exists (select 1 from public.properties p where p.id = sketch_photos.property_id and (p.user_id = (select auth.uid()) or ((select auth.jwt()) ->> 'email' = 'urbanfolduk@gmail.com'))));

alter table public.room_photos enable row level security;
drop policy if exists urbanfold_manage on public.room_photos;
create policy urbanfold_manage on public.room_photos for all to authenticated
  using (exists (select 1 from public.rooms r join public.properties p on p.id = r.property_id where r.id = room_photos.room_id and (p.user_id = (select auth.uid()) or ((select auth.jwt()) ->> 'email' = 'urbanfolduk@gmail.com')))) with check (exists (select 1 from public.rooms r join public.properties p on p.id = r.property_id where r.id = room_photos.room_id and (p.user_id = (select auth.uid()) or ((select auth.jwt()) ->> 'email' = 'urbanfolduk@gmail.com'))));

drop policy if exists urbanfold_storage_select on storage.objects;
create policy urbanfold_storage_select on storage.objects for select to authenticated
  using (bucket_id in ('exterior-photos','sketch-photos','room-photos') and exists (select 1 from public.properties p where p.id::text = (storage.foldername(name))[1] and (p.user_id = (select auth.uid()) or ((select auth.jwt()) ->> 'email' = 'urbanfolduk@gmail.com'))));

drop policy if exists urbanfold_storage_insert on storage.objects;
create policy urbanfold_storage_insert on storage.objects for insert to authenticated
  with check (bucket_id in ('exterior-photos','sketch-photos','room-photos') and exists (select 1 from public.properties p where p.id::text = (storage.foldername(name))[1] and (p.user_id = (select auth.uid()) or ((select auth.jwt()) ->> 'email' = 'urbanfolduk@gmail.com'))));

-- Stop rather than silently retain an additional permissive policy.
do $$
begin
  if exists (select 1 from pg_policies where
    ((schemaname = 'public' and tablename in ('properties','extensions','rooms',
      'exterior_photos','extension_photos','sketch_photos','room_photos'))
      or (schemaname = 'storage' and tablename = 'objects'))
    and not (
      (schemaname = 'public' and tablename = 'properties' and policyname in
        ('urbanfold_properties_select','urbanfold_properties_insert','urbanfold_properties_update'))
      or (schemaname = 'public' and tablename in ('extensions','rooms','exterior_photos',
        'extension_photos','sketch_photos','room_photos') and policyname = 'urbanfold_manage')
      or (schemaname = 'storage' and tablename = 'objects' and policyname in
        ('urbanfold_storage_select','urbanfold_storage_insert'))
    )) then
    raise exception 'Additional access policies exist. Review them before applying this change.';
  end if;
  if (select count(*) from storage.buckets where id in ('exterior-photos','sketch-photos','room-photos') and not public) <> 3 then
    raise exception 'All three survey photo buckets must exist and remain private.';
  end if;
end $$;

commit;

-- Confirmation contains no survey records.
select 'Urbanfold access policies applied; survey records and photos preserved.' as result;
