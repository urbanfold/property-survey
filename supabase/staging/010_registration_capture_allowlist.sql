-- PROPOSED STAGING ONLY, NOT EXECUTED. Verify project hexhtduvqzleoazusskh.
-- No Auth/consent/queue/survey/photo/credit row is created or changed here.
-- Creates one private allowlist row for the explicitly approved self-signup.
-- Guarded single installation: fails on rerun or unexpected capture source.
begin;
do $$ begin
 if current_user<>'postgres' or auth.uid() is not null or auth.jwt()->>'role' is not null then
  raise exception 'Staging postgres session without simulated JWT claims required.';
 end if;
 if obj_description(to_regclass('public.properties'),'pg_class') is distinct from
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.' then
  raise exception 'Reviewed staging baseline required. Verify hexhtduvqzleoazusskh independently.';
 end if;
 if not exists(select 1 from pg_proc p where p.oid=to_regprocedure('public.capture_staging_notification(text,uuid,jsonb)')
   and p.prosecdef and pg_get_userbyid(p.proowner)='postgres'
   and encode(sha256(convert_to(btrim(replace(p.prosrc,E'\r\n',E'\n'),E' \t\n\r'),'UTF8')),'hex')='058e070f06b12600d2408f1975c8e8b9780f6dfa5659b5a811b99680dddfb6c8'
   and exists(select 1 from unnest(p.proconfig) s where s in('search_path=""','search_path='))) then
  raise exception 'Capture helper differs from reviewed source. Stop and inspect; never overwrite unknown code.';
 end if;
 if to_regclass('public.staging_registration_capture_allowlist') is not null then
  raise exception 'Allowlist already exists; do not rerun or reset it.';
 end if;
 if not exists(select 1 from auth.users u join public.registration_notification_events e on e.user_id=u.id
  where u.id='b83f87d8-abf2-4800-beab-8279917804c7'::uuid
  and u.email='urbanfolduk+staging-reg-01@gmail.com' and u.email_confirmed_at is not null
  and e.registration_email=u.email and e.state='pending' and e.newsletter_signup_choice is true)
 or exists(select 1 from public.staging_notification_receipts r join public.registration_notification_events e on r.delivery_id=e.id
  where r.kind='registration_verified' and e.user_id='b83f87d8-abf2-4800-beab-8279917804c7'::uuid) then
  raise exception 'Exact verified test identity/pending unconsumed event not present; inspect current metadata.';
 end if;
end $$;
create table public.staging_registration_capture_allowlist(
 user_id uuid primary key references auth.users(id) on delete cascade,
 registration_email text not null unique,
 enabled boolean not null default false,
 approved_at timestamptz not null default clock_timestamp()
);
alter table public.staging_registration_capture_allowlist enable row level security;
revoke all on public.staging_registration_capture_allowlist from public,anon,authenticated,service_role;
grant select on public.staging_registration_capture_allowlist to service_role;
insert into public.staging_registration_capture_allowlist(user_id,registration_email,enabled)
 values('b83f87d8-abf2-4800-beab-8279917804c7','urbanfolduk+staging-reg-01@gmail.com',true);
create or replace function public.capture_staging_notification(kind text,delivery_id uuid,payload jsonb)
returns void language plpgsql security definer set search_path='' as $$
declare person uuid; approved_registration boolean:=false;
begin
 if obj_description('public.properties'::regclass,'pg_class') is distinct from
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.' then raise exception 'STAGING_REQUIRED';end if;
 if kind='survey' then
  select p.user_id into person from public.properties p where p.id=(payload->>'property_id')::uuid and p.address like 'DUMMY%';
  if coalesce(payload->>'client_email','') not like '%@example.invalid' then raise exception 'DUMMY_RECIPIENT_REQUIRED';end if;
 elsif kind='registration_verified' then
  person:=(payload->>'user_id')::uuid;
  -- The only exception to the legacy invalid-domain rule is an owner-approved
  -- exact identity pair AND its real, already-claimed registration event.
  approved_registration:=exists(
   select 1 from public.staging_registration_capture_allowlist a
   join auth.users u on u.id=a.user_id and u.email=a.registration_email
   join public.registration_notification_events e on e.user_id=u.id
   where a.enabled and a.user_id=person
   and a.registration_email=payload->>'registration_email'
   and u.email_confirmed_at is not null
   and e.id=delivery_id and e.registration_email=a.registration_email
   and e.state in ('sending','accepted','uncertain') and e.claim_started_at is not null
   and payload->>'id'=e.id::text
   and payload->>'notification_type'='registration_verified'
   and payload->>'recipient'='urbanfolduk@gmail.com'
   and (payload->>'registered_at')::timestamptz=e.registered_at
   and (payload->>'verified_at')::timestamptz=e.verified_at
   and payload->'newsletter_signup_choice'=to_jsonb(e.newsletter_signup_choice)
   and payload->'newsletter_opted_in_at_verification'=to_jsonb(e.newsletter_opted_in_at_verification)
  );
  if coalesce(payload->>'registration_email','') not like '%@example.invalid'
   and not approved_registration then raise exception 'DUMMY_REGISTRATION_REQUIRED';end if;
 else raise exception 'INVALID_KIND';end if;
 if not approved_registration and not exists(select 1 from auth.users u where u.id=person and u.email like '%@example.invalid') then raise exception 'DUMMY_USER_REQUIRED';end if;
 insert into public.staging_notification_receipts as r(kind,delivery_id,payload) values(kind,delivery_id,payload)
 on conflict on constraint staging_notification_receipts_pkey do update set attempts=r.attempts+1;
end $$;
revoke all on function public.capture_staging_notification(text,uuid,jsonb) from public,anon,authenticated;
grant execute on function public.capture_staging_notification(text,uuid,jsonb) to service_role;
commit;
