-- GENERATED DUMMY FIXTURE; NEVER EXECUTE ON SUPABASE
do $$begin if current_database()<>'urbanfold_acl_rehearsal' or inet_server_addr() is not null then raise exception 'LOCAL REHEARSAL DATABASE ONLY';end if;end $$;
-- Isolated test database, modelled on the user's 2026-10-22 diagnostics.
-- Never run this fixture against the live Supabase project.
create role anon nologin;
create role authenticated nologin;
create role service_role nologin bypassrls;
create schema auth;
create schema storage;
create function auth.jwt() returns jsonb language sql stable as $$
 select coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb
$$;
create function auth.uid() returns uuid language sql stable as $$
 select nullif(auth.jwt()->>'sub', '')::uuid
$$;
create function storage.foldername(name text) returns text[] language sql immutable as $$
 select (string_to_array(name, '/'))[1:array_length(string_to_array(name, '/'), 1)-1]
$$;
create table auth.users(id uuid primary key);
create table public.properties(
 id uuid primary key default gen_random_uuid(), user_id uuid references auth.users(id) on delete cascade,
 surveyor_name text, address text not null, postcode text not null, property_type text,
 notes text, status text default 'in_progress', created_at timestamptz default now(), client_email text
);
create table public.extensions(id uuid primary key default gen_random_uuid(),
 property_id uuid references public.properties(id) on delete cascade, extension_types jsonb, description text,
 width numeric(5,2), length numeric(5,2), created_at timestamptz default now());
create table public.rooms(id uuid primary key default gen_random_uuid(),
 property_id uuid references public.properties(id) on delete cascade, room_name text not null, shape text,
 dimensions jsonb, additional_measurements text, created_at timestamptz default now());
create table public.exterior_photos(id uuid primary key default gen_random_uuid(),
 property_id uuid references public.properties(id) on delete cascade, elevation_type text not null, photo_url text not null,
 created_at timestamptz default now());
create table public.extension_photos(id uuid primary key default gen_random_uuid(),
 property_id uuid references public.properties(id) on delete cascade, photo_url text not null, created_at timestamptz default now());
create table public.sketch_photos(id uuid primary key default gen_random_uuid(),
 property_id uuid references public.properties(id) on delete cascade, photo_url text not null, created_at timestamptz default now());
create table public.room_photos(id uuid primary key default gen_random_uuid(),
 room_id uuid references public.rooms(id) on delete cascade, photo_url text not null, created_at timestamptz default now());
create table storage.buckets(id text primary key, public boolean not null default false);
create table storage.objects(id uuid primary key default gen_random_uuid(),
 bucket_id text references storage.buckets(id), name text not null);
alter table storage.objects enable row level security;
insert into storage.buckets values('exterior-photos',false),('sketch-photos',false),('room-photos',false);
grant usage on schema auth, storage, public to anon, authenticated;
grant execute on all functions in schema auth, storage to anon, authenticated;
grant select, insert, update, delete on all tables in schema public, storage to anon, authenticated;

-- Reproduce broad legacy rules from the diagnostic result; migration must remove them.
alter table public.properties enable row level security;
create policy "Allow users to view properties" on public.properties for select to authenticated using (true);
create policy "Allow users to update properties" on public.properties for update to authenticated using (true);
create policy "Allow users to insert properties" on public.properties for insert to authenticated with check (true);
create policy "Allow public access to view photos" on storage.objects for select using (true);
create policy "Public Access for Photos" on storage.objects for select using (true);
create policy "Allow authenticated users to upload photos" on storage.objects for insert to authenticated with check (true);

-- LOCAL TEST DEFAULTS ONLY: model broad defaults so preservation is exercised.
alter default privileges for role postgres in schema public grant all on tables to anon,authenticated,service_role;
alter default privileges for role postgres in schema public grant execute on functions to anon,authenticated,service_role;
alter default privileges for role postgres in schema public grant all on sequences to anon,authenticated,service_role;
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

grant all on table public.properties, public.extensions, public.rooms, public.exterior_photos, public.extension_photos, public.sketch_photos, public.room_photos to anon,authenticated,service_role;
grant usage on schema auth,storage,public to service_role;
grant all on storage.objects,storage.buckets to service_role;
create role acl_rehearsal_probe nologin;
create role acl_rehearsal_delegate nologin;

insert into auth.users(id)values('e0000000-0000-4000-8000-000000000001'),('e0000000-0000-4000-8000-000000000002');
insert into public.properties(id,user_id,address,postcode,client_email)values
 ('e1000000-0000-4000-8000-000000000001','e0000000-0000-4000-8000-000000000001','DUMMY HOUSE A','ZZ1','a@unit.example.invalid'),
 ('e1000000-0000-4000-8000-000000000002','e0000000-0000-4000-8000-000000000002','DUMMY HOUSE B','ZZ2','b@unit.example.invalid');
insert into public.extensions(id,property_id,width,length)values('e2000000-0000-4000-8000-000000000001','e1000000-0000-4000-8000-000000000001',3.25,4.50);
insert into public.rooms(id,property_id,room_name,dimensions)values('e3000000-0000-4000-8000-000000000001','e1000000-0000-4000-8000-000000000001','DUMMY ROOM','{"l":"3.25","w":"4.50","h":"2.40"}');
insert into public.exterior_photos(property_id,elevation_type,photo_url)values('e1000000-0000-4000-8000-000000000001','front','storage://exterior-photos/e1000000-0000-4000-8000-000000000001/dummy.png');
insert into public.extension_photos(property_id,photo_url)values('e1000000-0000-4000-8000-000000000001','storage://exterior-photos/e1000000-0000-4000-8000-000000000001/dummy-extension.png');
insert into public.sketch_photos(property_id,photo_url)values('e1000000-0000-4000-8000-000000000001','storage://sketch-photos/e1000000-0000-4000-8000-000000000001/dummy.png');
insert into public.room_photos(room_id,photo_url)values('e3000000-0000-4000-8000-000000000001','storage://room-photos/e1000000-0000-4000-8000-000000000001/dummy.png');
insert into storage.objects(bucket_id,name)values('room-photos','e1000000-0000-4000-8000-000000000001/dummy.png');
insert into public.survey_free_allocations(user_id,property_id)values('e0000000-0000-4000-8000-000000000001','e1000000-0000-4000-8000-000000000001');
insert into public.survey_credit_purchases(checkout_session_id,payment_intent_id,user_id,amount_total,currency,live_mode)
 values('cs_live_LOCALDUMMY','pi_LOCALDUMMY','e0000000-0000-4000-8000-000000000001',600,'gbp',true);
