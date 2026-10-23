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
