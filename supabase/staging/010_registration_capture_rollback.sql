-- PROPOSED ROLLBACK ONLY; separate approval. Staging hexhtduvqzleoazusskh.
-- Pause registration dispatcher first with configuration approval. No data deletion.
-- Restores the reviewed 005 capture body, keeps the private allowlist/evidence.
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
   and encode(sha256(convert_to(btrim(replace(p.prosrc,E'\r\n',E'\n'),E' \t\n\r'),'UTF8')),'hex')='a0a932e15140581b19189404dcb42d2d36190ce7bb3f27b4199b9ee9a84995c7'
   and exists(select 1 from unnest(p.proconfig) s where s in('search_path=""','search_path='))) then
  raise exception 'Capture helper differs from reviewed source. Stop and inspect; never overwrite unknown code.';
 end if;
end $$;
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
