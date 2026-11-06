"""Generate a staging-only exact-pair exception and guarded rollback. No DB calls."""
from pathlib import Path
import re,hashlib,argparse
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='Generate staging allowlist SQL only; never execute SQL.')
parser.add_argument('--check',action='store_true')
CHECK=parser.parse_args().check
def emit(relative,text):
 p=root/relative
 if CHECK:
  if not p.exists() or p.read_text()!=text:raise SystemExit('Stale generated file: '+relative)
 else:
  p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
old=(root/'supabase/staging/005_dummy_notification_receiver.sql').read_text()
match=re.search(r'(create or replace function public\.capture_staging_notification\(.*?\$\$;)',old,re.S)
assert match
oldfn=match.group(1)
oldbody=re.search(r'as \$\$(.*?)\$\$;',oldfn,re.S).group(1)
newfn=oldfn.replace('declare person uuid;','declare person uuid; approved_registration boolean:=false;')
needle="  if coalesce(payload->>'registration_email','') not like '%@example.invalid' then raise exception 'DUMMY_REGISTRATION_REQUIRED';end if;"
replacement="""  -- The only exception to the legacy invalid-domain rule is an owner-approved
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
   and not approved_registration then raise exception 'DUMMY_REGISTRATION_REQUIRED';end if;"""
assert needle in newfn
newfn=newfn.replace(needle,replacement)
newfn=newfn.replace("if not exists(select 1 from auth.users u where u.id=person and u.email like '%@example.invalid') then", "if not approved_registration and not exists(select 1 from auth.users u where u.id=person and u.email like '%@example.invalid') then")
newbody=re.search(r'as \$\$(.*?)\$\$;',newfn,re.S).group(1)
oldhash=hashlib.sha256(oldbody.strip().replace('\r\n','\n').encode()).hexdigest()
newhash=hashlib.sha256(newbody.strip().replace('\r\n','\n').encode()).hexdigest()
baseguard=""" if current_user<>'postgres' or auth.uid() is not null or auth.jwt()->>'role' is not null then
  raise exception 'Staging postgres session without simulated JWT claims required.';
 end if;
 if obj_description(to_regclass('public.properties'),'pg_class') is distinct from
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.' then
  raise exception 'Reviewed staging baseline required. Verify hexhtduvqzleoazusskh independently.';
 end if;
"""
def functionguard(expected):return f""" if not exists(select 1 from pg_proc p where p.oid=to_regprocedure('public.capture_staging_notification(text,uuid,jsonb)')
   and p.prosecdef and pg_get_userbyid(p.proowner)='postgres'
   and encode(sha256(convert_to(btrim(replace(p.prosrc,E'\\r\\n',E'\\n'),E' \\t\\n\\r'),'UTF8')),'hex')='{expected}'
   and exists(select 1 from unnest(p.proconfig) s where s in('search_path=\"\"','search_path='))) then
  raise exception 'Capture helper differs from reviewed source. Stop and inspect; never overwrite unknown code.';
 end if;
"""
header="""-- PROPOSED STAGING ONLY, NOT EXECUTED. Verify project hexhtduvqzleoazusskh.
-- No Auth/consent/queue/survey/photo/credit row is created or changed here.
-- Creates one private allowlist row for the explicitly approved self-signup.
-- Guarded single installation: fails on rerun or unexpected capture source.
begin;
do $$ begin
"""
checks=""" if to_regclass('public.staging_registration_capture_allowlist') is not null then
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
"""
privs="""
revoke all on function public.capture_staging_notification(text,uuid,jsonb) from public,anon,authenticated;
grant execute on function public.capture_staging_notification(text,uuid,jsonb) to service_role;
commit;
"""
emit('supabase/staging/010_registration_capture_allowlist.sql',header+baseguard+functionguard(oldhash)+checks+newfn+privs)
rollback="""-- PROPOSED ROLLBACK ONLY; separate approval. Staging hexhtduvqzleoazusskh.
-- Pause registration dispatcher first with configuration approval. No data deletion.
-- Restores the reviewed 005 capture body, keeps the private allowlist/evidence.
begin;
do $$ begin
"""+baseguard+functionguard(newhash)+"end $$;\n"+oldfn+privs
emit('supabase/staging/010_registration_capture_rollback.sql',rollback)
emit('audits/2026-11-06/registration-capture-allowlist/capture-body-hashes.json',__import__('json').dumps({'original005_body_sha256_normalized':oldhash,'allowlist_body_sha256_normalized':newhash},indent=2)+'\n')
