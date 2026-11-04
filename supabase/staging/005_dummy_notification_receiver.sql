-- STAGING ONLY, additive, not executed in cloud. Never install on production.
begin;
do $$ begin
 if obj_description('public.properties'::regclass,'pg_class') is distinct from
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.' then
  raise exception 'Reviewed staging baseline required.';
 end if;
end $$;
create table if not exists public.staging_notification_receipts(
 kind text not null check(kind in('survey','registration_verified')),
 delivery_id uuid not null,
 payload jsonb not null,
 attempts integer not null default 1 check(attempts>0),
 captured_at timestamptz not null default clock_timestamp(),
 primary key(kind,delivery_id)
);
alter table public.staging_notification_receipts enable row level security;
revoke all on public.staging_notification_receipts from public,anon,authenticated;
grant all on public.staging_notification_receipts to service_role;
create or replace function public.capture_staging_notification(kind text,delivery_id uuid,payload jsonb)
returns void language plpgsql security definer set search_path='' as $$
declare person uuid;
begin
 if obj_description('public.properties'::regclass,'pg_class') is distinct from
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.' then raise exception 'STAGING_REQUIRED';end if;
 if kind='survey' then
  select p.user_id into person from public.properties p where p.id=(payload->>'property_id')::uuid and p.address like 'DUMMY%';
  if coalesce(payload->>'client_email','') not like '%@example.invalid' then raise exception 'DUMMY_RECIPIENT_REQUIRED';end if;
 elsif kind='registration_verified' then
  person:=(payload->>'user_id')::uuid;
  if coalesce(payload->>'registration_email','') not like '%@example.invalid' then raise exception 'DUMMY_REGISTRATION_REQUIRED';end if;
 else raise exception 'INVALID_KIND';end if;
 if not exists(select 1 from auth.users u where u.id=person and u.email like '%@example.invalid') then raise exception 'DUMMY_USER_REQUIRED';end if;
 insert into public.staging_notification_receipts as r(kind,delivery_id,payload) values(kind,delivery_id,payload)
 on conflict on constraint staging_notification_receipts_pkey do update set attempts=r.attempts+1;
end $$;
revoke all on function public.capture_staging_notification(text,uuid,jsonb) from public,anon,authenticated;
grant execute on function public.capture_staging_notification(text,uuid,jsonb) to service_role;
commit;
