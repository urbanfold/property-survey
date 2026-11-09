-- PREPARED ONLY: fresh Urbanfold-Survey-Staging project after owner approval.
-- Never run tests/database_fixture.sql in Supabase. This baseline uses managed Auth/Storage.
-- Refuses an existing app schema/bucket rather than changing it or hiding drift.
begin;
do $$
begin
  if current_setting('urbanfold.staging_setup', true) is distinct from 'Urbanfold-Survey-Staging' then
    raise exception 'Staging acknowledgement missing. Review the staging guide first.';
  end if;
  if to_regclass('auth.users') is null or to_regclass('storage.objects') is null
     or to_regclass('storage.buckets') is null
     or to_regprocedure('auth.uid()') is null or to_regprocedure('auth.jwt()') is null
     or to_regprocedure('storage.foldername(text)') is null then
    raise exception 'Expected Supabase-managed Auth and Storage are unavailable.';
  end if;
  if exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace
      where n.nspname='public' and c.relname in
      ('properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos',
       'survey_free_allocations','survey_credit_purchases','survey_credit_revocations','survey_notification_events'))
     or exists(select 1 from storage.buckets where id in ('exterior-photos','sketch-photos','room-photos'))
     or exists(select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
      where n.nspname='public' and p.proname in ('get_survey_allowance','enforce_survey_allowance',
        'protect_survey_address','record_survey_purchase','revoke_survey_purchase',
        'claim_survey_notification','finish_survey_notification')) then
    raise exception 'Existing Urbanfold objects found. Stop: this is a fresh-project baseline, not a repair/reset script.';
  end if;
  if exists(select 1 from pg_policies where schemaname='storage' and tablename='objects') then
    raise exception 'Existing Storage object policies found. Review before staging setup.';
  end if;
end $$;

-- The seven original table columns follow the historical column diagnostics.
-- PK/FK definitions are the fixture/source reconstruction, pending production metadata.
create table public.properties(
 id uuid primary key default gen_random_uuid(), user_id uuid references auth.users(id),
 surveyor_name text, address text not null, postcode text not null, property_type text,
 notes text, status text default 'in_progress', created_at timestamptz default now(), client_email text
);
create table public.extensions(id uuid primary key default gen_random_uuid(),
 property_id uuid references public.properties(id), extension_types jsonb, description text,
 width numeric, length numeric, created_at timestamptz default now());
create table public.rooms(id uuid primary key default gen_random_uuid(),
 property_id uuid references public.properties(id), room_name text not null, shape text,
 dimensions jsonb, additional_measurements text, created_at timestamptz default now());
create table public.exterior_photos(id uuid primary key default gen_random_uuid(),
 property_id uuid references public.properties(id), elevation_type text not null, photo_url text not null,
 created_at timestamptz default now());
create table public.extension_photos(id uuid primary key default gen_random_uuid(),
 property_id uuid references public.properties(id), photo_url text not null, created_at timestamptz default now());
create table public.sketch_photos(id uuid primary key default gen_random_uuid(),
 property_id uuid references public.properties(id), photo_url text not null, created_at timestamptz default now());
create table public.room_photos(id uuid primary key default gen_random_uuid(),
 room_id uuid references public.rooms(id), photo_url text not null, created_at timestamptz default now());

comment on table public.properties is 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.';

-- Fail closed before any subsequent migration commits: no anonymous table access.
alter table public.properties enable row level security;
alter table public.extensions enable row level security;
alter table public.rooms enable row level security;
alter table public.exterior_photos enable row level security;
alter table public.extension_photos enable row level security;
alter table public.sketch_photos enable row level security;
alter table public.room_photos enable row level security;
revoke all on public.properties,public.extensions,public.rooms,public.exterior_photos,
 public.extension_photos,public.sketch_photos,public.room_photos from public,anon,authenticated;
grant usage on schema public to authenticated,service_role;
grant select,insert,update on public.properties to authenticated;
grant select,insert,update,delete on public.extensions,public.rooms,public.exterior_photos,
 public.extension_photos,public.sketch_photos,public.room_photos to authenticated;
grant all on public.properties,public.extensions,public.rooms,public.exterior_photos,
 public.extension_photos,public.sketch_photos,public.room_photos to service_role;

-- Proposed nonunique staging indexes: do not alter duplicate/entitlement rules.
create index urbanfold_properties_owner_created on public.properties(user_id,created_at,id);
create index urbanfold_extensions_property_created on public.extensions(property_id,created_at,id);
create index urbanfold_rooms_property_created on public.rooms(property_id,created_at,id);
create index urbanfold_exterior_property_created on public.exterior_photos(property_id,created_at,id);
create index urbanfold_extension_photos_property_created on public.extension_photos(property_id,created_at,id);
create index urbanfold_sketch_property_created on public.sketch_photos(property_id,created_at,id);
create index urbanfold_room_photos_room_created on public.room_photos(room_id,created_at,id);

-- Insert bucket configuration only; never insert file rows into storage.objects.
-- Null limits mirror the historical diagnostic, not a claim of sufficient upload hardening.
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types) values
 ('exterior-photos','exterior-photos',false,null,null),
 ('sketch-photos','sketch-photos',false,null,null),
 ('room-photos','room-photos',false,null,null);
-- Table ACLs for managed Storage are supplied by Supabase, not recreated by this script.
-- Migration 001 adds only owner/admin SELECT and INSERT policies for object paths.
commit;
