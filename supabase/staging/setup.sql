-- GENERATED, PREPARED ONLY. NOT AUTHORISED FOR EXECUTION.
-- Source: scripts/build_staging_setup.py. Fresh staging only; do not use on production.
-- BEFORE APPROVED EXECUTION: manually verify the project URL/reference in Dashboard.
-- This acknowledgement is an operator interlock, NOT project-identity verification.
-- Each source migration has its own transaction. Stop on the first error.
set urbanfold.staging_setup = 'Urbanfold-Survey-Staging';

-- BEGIN SOURCE supabase/staging/000_fresh_baseline.sql
-- SHA256 8d9601f1f06088e85e8e021aec595318619e644bb744cc6a748fe1edb22fcf73
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

-- END SOURCE supabase/staging/000_fresh_baseline.sql

-- BEGIN SOURCE supabase/001_secure_access.sql
-- SHA256 10d0d24509612550342110d0e7d6317ebb18bc7966b688850571aa4c6c902864
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

-- END SOURCE supabase/001_secure_access.sql

-- BEGIN SOURCE supabase/002_survey_purchases.sql
-- SHA256 740791bf6e8aa77f6a8ab16b06e284f707f4599417bdf3f21805da02b961c0bf
-- One lifetime free survey per client account; verified £6 purchases add one credit.
-- Existing surveys are preserved. Apply 001_secure_access.sql first.
begin;
create table if not exists public.survey_free_allocations (
  user_id uuid primary key references auth.users(id) on delete cascade,
  property_id uuid not null unique,
  allocated_at timestamptz not null default now()
);
create table if not exists public.survey_credit_revocations (
  payment_intent_id text primary key,
  reason text not null,
  recorded_at timestamptz not null default now()
);
create table if not exists public.survey_credit_purchases (
  checkout_session_id text primary key,
  payment_intent_id text not null unique,
  user_id uuid not null references auth.users(id) on delete cascade,
  amount_total integer not null check (amount_total = 600),
  currency text not null check (currency = 'gbp'),
  live_mode boolean not null,
  purchased_at timestamptz not null default now(),
  redeemed_property_id uuid unique,
  redeemed_at timestamptz
);
-- Deliberately keep allocation/redemption UUIDs if a property is removed by an
-- administrator: deleting a property must not generate another free/paid credit.
insert into public.survey_free_allocations(user_id, property_id)
select distinct on (user_id) user_id, id from public.properties
where user_id is not null order by user_id, created_at asc nulls first, id
on conflict (user_id) do nothing;

alter table public.properties add column if not exists address_locked boolean not null default false;
update public.properties set address_locked = true where last_submitted_at is not null and not address_locked;

alter table public.survey_free_allocations enable row level security;
alter table public.survey_credit_purchases enable row level security;
alter table public.survey_credit_revocations enable row level security;
revoke all on public.survey_free_allocations, public.survey_credit_purchases, public.survey_credit_revocations from anon, authenticated;
grant select on public.survey_free_allocations, public.survey_credit_purchases to authenticated;
grant all on public.survey_free_allocations, public.survey_credit_purchases, public.survey_credit_revocations to service_role;
drop policy if exists urbanfold_free_read on public.survey_free_allocations;
create policy urbanfold_free_read on public.survey_free_allocations for select to authenticated
using (user_id = (select auth.uid()) or (select auth.jwt())->>'email' = 'urbanfolduk@gmail.com');
drop policy if exists urbanfold_purchase_read on public.survey_credit_purchases;
create policy urbanfold_purchase_read on public.survey_credit_purchases for select to authenticated
using (user_id = (select auth.uid()) or (select auth.jwt())->>'email' = 'urbanfolduk@gmail.com');

create or replace function public.get_survey_allowance()
returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  person uuid := auth.uid();
  is_admin boolean := coalesce(auth.jwt()->>'email' = 'urbanfolduk@gmail.com', false);
  free_available boolean;
  credits bigint;
begin
  if person is null then raise exception 'Sign in to check your survey allowance.'; end if;
  select not exists(select 1 from public.survey_free_allocations where user_id = person) into free_available;
  select count(*) into credits from public.survey_credit_purchases p
    where p.user_id = person and p.live_mode and p.redeemed_property_id is null
      and not exists(select 1 from public.survey_credit_revocations r where r.payment_intent_id = p.payment_intent_id);
  return jsonb_build_object('unlimited', is_admin, 'free_available', free_available,
    'paid_credits', credits, 'can_create', is_admin or free_available or credits > 0,
    'price_pence', 600, 'currency', 'GBP');
end $$;
revoke all on function public.get_survey_allowance() from public, anon;
grant execute on function public.get_survey_allowance() to authenticated;

create or replace function public.enforce_survey_allowance()
returns trigger language plpgsql security definer set search_path = '' as $$
declare
  allocated uuid;
  purchase text;
  caller_role text := auth.jwt()->>'role';
begin
  -- Privileged maintenance and the existing signed admin identity are exempt.
  if caller_role = 'service_role' or (caller_role is null and auth.uid() is null)
     or (auth.uid() is not null and auth.jwt()->>'email' = 'urbanfolduk@gmail.com') then return new; end if;
  if auth.uid() is null or new.user_id is distinct from auth.uid() then
    raise exception 'Survey ownership is invalid.' using errcode = '42501';
  end if;
  -- Serialise concurrent first-survey creation and credit redemption per account.
  perform 1 from auth.users where id = new.user_id for update;
  -- A retry/upsert of the same property must not consume another credit.
  if exists(select 1 from public.properties where id = new.id and user_id = new.user_id) then return new; end if;
  insert into public.survey_free_allocations(user_id, property_id) values(new.user_id, new.id)
    on conflict(user_id) do nothing returning user_id into allocated;
  if allocated is not null then return new; end if;
  select p.checkout_session_id into purchase from public.survey_credit_purchases p
    where p.user_id = new.user_id and p.live_mode and p.redeemed_property_id is null
      and not exists(select 1 from public.survey_credit_revocations r where r.payment_intent_id = p.payment_intent_id)
    order by p.purchased_at, p.checkout_session_id for update limit 1;
  if purchase is null then raise exception 'URBANFOLD_SURVEY_LIMIT' using errcode = 'P0001'; end if;
  update public.survey_credit_purchases set redeemed_property_id = new.id, redeemed_at = now()
    where checkout_session_id = purchase;
  return new;
end $$;
revoke all on function public.enforce_survey_allowance() from public, anon, authenticated;
drop trigger if exists urbanfold_survey_allowance on public.properties;
create trigger urbanfold_survey_allowance before insert on public.properties
for each row execute function public.enforce_survey_allowance();

create or replace function public.protect_survey_address()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  if (auth.jwt()->>'role') = 'authenticated' and coalesce(auth.jwt()->>'email','') <> 'urbanfolduk@gmail.com' then
    if (old.address_locked or old.last_submitted_at is not null) and (
      lower(regexp_replace(trim(old.address), '\s+', ' ', 'g')) is distinct from lower(regexp_replace(trim(new.address), '\s+', ' ', 'g'))
      or upper(regexp_replace(old.postcode, '\s+', '', 'g')) is distinct from upper(regexp_replace(new.postcode, '\s+', '', 'g'))
    ) then raise exception 'URBANFOLD_ADDRESS_LOCKED' using errcode = 'P0001'; end if;
    new.address_locked := old.address_locked or old.last_submitted_at is not null or new.last_submitted_at is not null;
  end if;
  return new;
end $$;
revoke all on function public.protect_survey_address() from public, anon, authenticated;
drop trigger if exists urbanfold_protect_address on public.properties;
create trigger urbanfold_protect_address before update on public.properties
for each row execute function public.protect_survey_address();

-- Only the payment server can record purchases. A browser redirect never grants credit.
create or replace function public.record_survey_purchase(
  session_id text, intent_id text, buyer_id uuid, paid_amount integer, paid_currency text, is_live boolean
) returns void language plpgsql security definer set search_path = '' as $$
declare existing public.survey_credit_purchases;
begin
  if session_id !~ '^cs_(test|live)_[A-Za-z0-9]+$' or intent_id !~ '^pi_[A-Za-z0-9]+$'
     or paid_amount <> 600 or paid_currency <> 'gbp' or is_live is null
     or (is_live and session_id !~ '^cs_live_') or (not is_live and session_id !~ '^cs_test_') then raise exception 'Invalid survey payment.'; end if;
  insert into public.survey_credit_purchases(checkout_session_id,payment_intent_id,user_id,amount_total,currency,live_mode)
    values(session_id,intent_id,buyer_id,paid_amount,paid_currency,is_live)
    on conflict(checkout_session_id) do nothing;
  select * into existing from public.survey_credit_purchases where checkout_session_id = session_id;
  if existing.user_id is distinct from buyer_id or existing.payment_intent_id is distinct from intent_id
     or existing.live_mode is distinct from is_live then raise exception 'Payment identity does not match.'; end if;
end $$;
revoke all on function public.record_survey_purchase(text,text,uuid,integer,text,boolean) from public, anon, authenticated;
grant execute on function public.record_survey_purchase(text,text,uuid,integer,text,boolean) to service_role;

create or replace function public.revoke_survey_purchase(intent_id text, revocation_reason text)
returns void language plpgsql security definer set search_path = '' as $$
begin
  if intent_id !~ '^pi_[A-Za-z0-9]+$' then raise exception 'Invalid payment reference.'; end if;
  insert into public.survey_credit_revocations(payment_intent_id,reason)
    values(intent_id,left(revocation_reason,100)) on conflict(payment_intent_id) do nothing;
end $$;
revoke all on function public.revoke_survey_purchase(text,text) from public, anon, authenticated;
grant execute on function public.revoke_survey_purchase(text,text) to service_role;
commit;
select 'Survey allowance installed: one free property per client; verified £6 purchases add one survey. Existing surveys preserved.' as result;

-- END SOURCE supabase/002_survey_purchases.sql

-- BEGIN SOURCE supabase/003_survey_notifications.sql
-- SHA256 9f9b7d32477d575665fda9c0839aaa1310853a7db2802fb6364b04bfbe1f3258
-- PROPOSED F02 migration. Not applied to production. Apply only after approval.
-- Additive notification bookkeeping; no changes to surveys, photos or £6 credits.
begin;
create table if not exists public.survey_notification_events (
 id uuid primary key default gen_random_uuid(),
 property_id uuid not null references public.properties(id) on delete cascade,
 actor_id uuid not null references auth.users(id) on delete cascade,
 submission_at timestamptz not null,
 content_fingerprint text not null check(content_fingerprint ~ '^[0-9a-f]{64}$'),
 state text not null default 'sending' check(state in ('sending','accepted','uncertain')),
 created_at timestamptz not null default now(),
 finished_at timestamptz,
 unique(property_id,submission_at),
 unique(property_id,content_fingerprint)
);
create index if not exists survey_notification_actor_time on public.survey_notification_events(actor_id,created_at);
alter table public.survey_notification_events enable row level security;
revoke all on public.survey_notification_events from public,anon,authenticated;
grant all on public.survey_notification_events to service_role;

-- Actor comes from verified Auth on the server, never from a browser body.
create or replace function public.claim_survey_notification(actor uuid, property uuid, revision timestamptz)
returns jsonb language plpgsql security definer set search_path='' as $$
declare
 p public.properties;
 e public.survey_notification_events;
 actor_email text;
 confirmed timestamptz;
 fingerprint text;
begin
 select email,email_confirmed_at into actor_email,confirmed from auth.users where id=actor;
 if actor_email is null or confirmed is null then raise exception 'NOTIFICATION_AUTH_REQUIRED' using errcode='42501'; end if;
 -- Serialise rolling actor caps across properties, then per-property claims.
 perform pg_advisory_xact_lock(hashtextextended(actor::text,0));
 select * into p from public.properties where id=property for update;
 if not found or (p.user_id is distinct from actor and actor_email <> 'urbanfolduk@gmail.com') then
  raise exception 'NOTIFICATION_NOT_ALLOWED' using errcode='42501';
 end if;
 if p.last_submitted_at is null or p.last_submitted_at is distinct from revision then
  raise exception 'NOTIFICATION_SUBMISSION_CHANGED';
 end if;
 -- Deduplicate unchanged content even when an owner presses Submit again and
 -- the completion timestamp changes. Signing URLs are not persisted or hashed.
 select encode(sha256(convert_to(jsonb_build_object(
  'property',to_jsonb(p)-'last_submitted_at'-'address_locked'-'created_at'-'status',
  'extensions',(select coalesce(jsonb_agg(to_jsonb(x)-'created_at' order by x.id),'[]'::jsonb) from public.extensions x where x.property_id=property),
  'rooms',(select coalesce(jsonb_agg(to_jsonb(x)-'created_at' order by x.id),'[]'::jsonb) from public.rooms x where x.property_id=property),
  'exterior',(select coalesce(jsonb_agg(to_jsonb(x)-'created_at' order by x.id),'[]'::jsonb) from public.exterior_photos x where x.property_id=property),
  'extension_photos',(select coalesce(jsonb_agg(to_jsonb(x)-'created_at' order by x.id),'[]'::jsonb) from public.extension_photos x where x.property_id=property),
  'sketches',(select coalesce(jsonb_agg(to_jsonb(x)-'created_at' order by x.id),'[]'::jsonb) from public.sketch_photos x where x.property_id=property),
  'room_photos',(select coalesce(jsonb_agg(to_jsonb(x)-'created_at' order by x.id),'[]'::jsonb) from public.room_photos x join public.rooms r on r.id=x.room_id where r.property_id=property)
 )::text,'UTF8')),'hex') into fingerprint;
 select * into e from public.survey_notification_events where property_id=property and content_fingerprint=fingerprint;
 if found then return jsonb_build_object('id',e.id,'state',e.state,'claimed',false); end if;
 if (select count(*) from public.survey_notification_events where actor_id=actor and created_at>now()-interval '24 hours')>=20
    or (select count(*) from public.survey_notification_events where property_id=property and created_at>now()-interval '24 hours')>=5 then
  raise exception 'NOTIFICATION_RATE_LIMIT';
 end if;
 if coalesce(trim(p.client_email),'') !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$' then
  raise exception 'NOTIFICATION_RECIPIENT_INVALID';
 end if;
 insert into public.survey_notification_events(property_id,actor_id,submission_at,content_fingerprint)
 values(property,actor,revision,fingerprint) returning * into e;
 return jsonb_build_object('id',e.id,'state',e.state,'claimed',true,
  'payload',jsonb_build_object('property_id',p.id,'client_email',trim(p.client_email),
   'address',p.address,'surveyor_name',p.surveyor_name));
end $$;
revoke all on function public.claim_survey_notification(uuid,uuid,timestamptz) from public,anon,authenticated;
grant execute on function public.claim_survey_notification(uuid,uuid,timestamptz) to service_role;

create or replace function public.finish_survey_notification(event uuid, accepted boolean)
returns void language plpgsql security definer set search_path='' as $$
begin
 update public.survey_notification_events set state=case when accepted then 'accepted' else 'uncertain' end,finished_at=now()
 where id=event and state='sending';
end $$;
revoke all on function public.finish_survey_notification(uuid,boolean) from public,anon,authenticated;
grant execute on function public.finish_survey_notification(uuid,boolean) to service_role;
commit;

-- END SOURCE supabase/003_survey_notifications.sql

-- Metadata-only completion marker; run verification queries separately.
select 'Prepared staging sequence completed; verify before dummy-user tests.' as result;
