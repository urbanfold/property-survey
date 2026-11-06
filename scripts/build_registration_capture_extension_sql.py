"""Generate guarded row-only staging upgrade/preflight/postcheck/rollback; no DB calls."""
from pathlib import Path
import argparse,json
ROOT=Path(__file__).resolve().parents[1]
PAIRS=[(1,'b83f87d8-abf2-4800-beab-8279917804c7','urbanfolduk+staging-reg-01@gmail.com'),(2,'d2598ebf-d44c-4e11-81a5-d82f3d06ada1','urbanfolduk+staging-reg-02@gmail.com'),(3,'3a4e8d72-bf58-468a-b24f-0417c4a64f5b','urbanfolduk+staging-reg-03@gmail.com')]
HASH=json.loads((ROOT/'audits/2026-11-06/registration-capture-allowlist/capture-body-hashes.json').read_text())['allowlist_body_sha256_normalized']
VALUES=',\n '.join(f"({n},'{u}'::uuid,'{e}'::text)" for n,u,e in PAIRS)
TARGETS=','.join(f"'{u}'::uuid" for _,u,_ in PAIRS[1:])
FIRST=PAIRS[0][1]
# Exact schema/ACL/source guard; no functions, roles, policies or tables are altered.
GUARD=f"""
 if current_user<>'postgres' or auth.uid() is not null or auth.jwt()->>'role' is not null then
  raise exception 'Staging postgres session without simulated JWT claims required.';
 end if;
 if obj_description(to_regclass('public.properties'),'pg_class') is distinct from
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.' then
  raise exception 'Reviewed staging baseline required. Verify hexhtduvqzleoazusskh independently.';
 end if;
 if not exists(select 1 from pg_proc p where p.oid=to_regprocedure('public.capture_staging_notification(text,uuid,jsonb)')
  and p.prosecdef and pg_get_userbyid(p.proowner)='postgres'
  and encode(sha256(convert_to(btrim(replace(p.prosrc,E'\\r\\n',E'\\n'),E' \\t\\n\\r'),'UTF8')),'hex')='{HASH}'
  and exists(select 1 from unnest(p.proconfig) s where s in('search_path=\"\"','search_path='))
  and not has_function_privilege('anon',p.oid,'EXECUTE')
  and not has_function_privilege('authenticated',p.oid,'EXECUTE')
  and has_function_privilege('service_role',p.oid,'EXECUTE')) then
  raise exception 'Capture source/owner/path/permissions differ from reviewed010. Stop; do not reinstall010.';
 end if;
 if not exists(select 1 from pg_class c where c.oid=to_regclass('public.staging_registration_capture_allowlist')
  and c.relkind='r' and c.relrowsecurity and pg_get_userbyid(c.relowner)='postgres') then
  raise exception 'Expected private010 allowlist table is missing or changed.';
 end if;
 if (select count(*) from pg_attribute a where a.attrelid='public.staging_registration_capture_allowlist'::regclass
  and a.attnum>0 and not a.attisdropped)<>4
 or (select count(*) from pg_attribute a where a.attrelid='public.staging_registration_capture_allowlist'::regclass
  and a.attnum>0 and not a.attisdropped and a.attnotnull and a.attgenerated='' and a.attidentity=''
  and (a.attname,a.atttypid) in (('user_id','uuid'::regtype),('registration_email','text'::regtype),('enabled','boolean'::regtype),('approved_at','timestamptz'::regtype)))<>4
 or (select count(*) from pg_constraint c where c.conrelid='public.staging_registration_capture_allowlist'::regclass and c.contype in('p','u','f'))<>3
 or exists(select 1 from pg_constraint c where c.conrelid='public.staging_registration_capture_allowlist'::regclass and c.contype not in('p','u','f','n')) then
  raise exception 'Allowlist columns/constraints differ from010; inspect before row changes.';
 end if;
 if not exists(select 1 from pg_constraint c join pg_attribute a on a.attrelid=c.conrelid and a.attnum=c.conkey[1]
  where c.conrelid='public.staging_registration_capture_allowlist'::regclass and c.contype='p' and cardinality(c.conkey)=1 and a.attname='user_id')
 or not exists(select 1 from pg_constraint c join pg_attribute a on a.attrelid=c.conrelid and a.attnum=c.conkey[1]
  where c.conrelid='public.staging_registration_capture_allowlist'::regclass and c.contype='u' and cardinality(c.conkey)=1 and a.attname='registration_email')
 or not exists(select 1 from pg_constraint c join pg_attribute a on a.attrelid=c.conrelid and a.attnum=c.conkey[1]
  join pg_attribute r on r.attrelid=c.confrelid and r.attnum=c.confkey[1]
  where c.conrelid='public.staging_registration_capture_allowlist'::regclass and c.contype='f' and cardinality(c.conkey)=1
  and c.confrelid='auth.users'::regclass and a.attname='user_id' and r.attname='id' and c.confdeltype='c' and c.convalidated) then
  raise exception 'Allowlist PK/unique/FK differs from010; stop without schema edits.';
 end if;
 if exists(select 1 from pg_trigger where tgrelid='public.staging_registration_capture_allowlist'::regclass and not tgisinternal)
 or exists(select 1 from pg_rewrite where ev_class='public.staging_registration_capture_allowlist'::regclass)
 or exists(select 1 from pg_policy where polrelid='public.staging_registration_capture_allowlist'::regclass)
 or has_table_privilege('anon','public.staging_registration_capture_allowlist','SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
 or has_table_privilege('authenticated','public.staging_registration_capture_allowlist','SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
 or not has_table_privilege('service_role','public.staging_registration_capture_allowlist','SELECT')
 or has_table_privilege('service_role','public.staging_registration_capture_allowlist','INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') then
  raise exception 'Unexpected allowlist trigger/rule/policy/grants; stop before INSERT/UPDATE.';
 end if;
 lock table public.staging_registration_capture_allowlist in share row exclusive mode;
 if not exists(select 1 from public.staging_registration_capture_allowlist where user_id='{FIRST}'::uuid
  and registration_email='{PAIRS[0][2]}' and enabled) then
  raise exception 'Test1 exact enabled entry missing or changed; never overwrite it.';
 end if;
"""
# Snapshot rows are held only in server memory; returned evidence is counts/booleans.
SNAP="""jsonb_build_object(
 'registration_events',(select coalesce(jsonb_agg(to_jsonb(t) order by t.id),'[]'::jsonb) from public.registration_notification_events t),
 'receipts',(select coalesce(jsonb_agg(to_jsonb(t) order by t.kind,t.delivery_id),'[]'::jsonb) from public.staging_notification_receipts t),
 'preferences',(select coalesce(jsonb_agg(to_jsonb(t) order by t.user_id),'[]'::jsonb) from public.newsletter_preferences t),
 'consent_audit',(select coalesce(jsonb_agg(to_jsonb(t) order by t.id),'[]'::jsonb) from public.newsletter_consent_events t),
 'survey_events',(select coalesce(jsonb_agg(to_jsonb(t) order by t.id),'[]'::jsonb) from public.survey_notification_events t),
 'free_allocations',(select coalesce(jsonb_agg(to_jsonb(t) order by t.user_id),'[]'::jsonb) from public.survey_free_allocations t),
 'purchases',(select coalesce(jsonb_agg(to_jsonb(t) order by t.checkout_session_id),'[]'::jsonb) from public.survey_credit_purchases t),
 'revocations',(select coalesce(jsonb_agg(to_jsonb(t) order by t.payment_intent_id),'[]'::jsonb) from public.survey_credit_revocations t)
)"""
BEFORE=f""" select to_jsonb(a) into first_before from public.staging_registration_capture_allowlist a where user_id='{FIRST}'::uuid;
 select {SNAP} into data_before;
"""
AFTER=f""" select to_jsonb(a) into first_after from public.staging_registration_capture_allowlist a where user_id='{FIRST}'::uuid;
 select {SNAP} into data_after;
 if first_before is distinct from first_after or data_before is distinct from data_after then
  raise exception 'Test1/history/consent/credit data changed unexpectedly; rollback this transaction.';
 end if;
"""
HEADER="""-- PROPOSAL ONLY: row-only upgrade of EXISTING010, staging hexhtduvqzleoazusskh.
-- Separate SQL approval required. No function/schema/policy/secret changes or sends.
-- Pause/avoid automatic dispatcher invocations before approval; never run010 again.
begin;
set local search_path=pg_catalog;
do $$
declare first_before jsonb;first_after jsonb;data_before jsonb;data_after jsonb;
begin
"""
install=HEADER+GUARD+f"""
 if (select count(*) from public.staging_registration_capture_allowlist)<>1 then
  raise exception 'Expected Test1 only. Already upgraded or unexpected entries: inspect; do not reset.';
 end if;
 -- Block competing claims for these pending events while eligibility is checked.
 perform e.id from public.registration_notification_events e where e.user_id in({TARGETS}) order by e.user_id for update;
 if (select count(*) from (values {VALUES}) wanted(n,user_id,email)
  join auth.users u on u.id=wanted.user_id and u.email=wanted.email and u.email_confirmed_at is not null
  join public.newsletter_preferences p on p.user_id=u.id and p.signup_opt_in_requested is false and p.opted_in is false
  join public.registration_notification_events e on e.user_id=u.id and e.registration_email=wanted.email
   and e.state='pending' and e.claim_started_at is null and e.newsletter_signup_choice is false
   and e.newsletter_opted_in_at_verification is false
  where wanted.n in(2,3)
   and (select count(*) from public.newsletter_consent_events a where a.user_id=u.id and a.action='signup_request')=1
   and (select count(*) from public.newsletter_consent_events a where a.user_id=u.id and a.action='email_verified')=1
   and not exists(select 1 from public.staging_notification_receipts r where r.kind='registration_verified' and r.delivery_id=e.id))<>2
 or (select count(*) from public.registration_notification_events where state='pending')<>2 then
  raise exception 'Exact verified false-consent identities, pending events/audit, zero captures or isolated pending queue differ; inspect.';
 end if;
"""+BEFORE+f""" insert into public.staging_registration_capture_allowlist(user_id,registration_email,enabled,approved_at)
 select user_id,email,true,clock_timestamp() from (values {VALUES}) wanted(n,user_id,email) where n in(2,3);
 if (select count(*) from public.staging_registration_capture_allowlist)<>3 then
  raise exception 'Unexpected resulting allowlist count; rollback.';
 end if;
"""+AFTER+"end $$;\ncommit;\n"
rollback=HEADER.replace('row-only upgrade','row-only rollback (disable added pairs, preserve evidence)')+GUARD+f"""
 if (select count(*) from public.staging_registration_capture_allowlist)<>3
 or (select count(*) from (values {VALUES}) wanted(n,user_id,email)
  join public.staging_registration_capture_allowlist a on a.user_id=wanted.user_id and a.registration_email=wanted.email where wanted.n in(2,3))<>2 then
  raise exception 'Expected exact three-entry allowlist. Stop; never modify unknown entries.';
 end if;
"""+BEFORE+f""" update public.staging_registration_capture_allowlist set enabled=false
 where (user_id,registration_email) in (select user_id,email from (values {VALUES}) wanted(n,user_id,email) where n in(2,3))
 and enabled;
"""+AFTER+"end $$;\ncommit;\n-- Both added rows retained disabled. Re-enable requires separate approval; no reset/reinstall.\n"
query=f"""-- SELECT ONLY. Verify project hexhtduvqzleoazusskh. No secrets or raw Auth data.
with wanted(n,user_id,email) as (values {VALUES})
select jsonb_build_object(
 'staging_marker_matches',obj_description(to_regclass('public.properties'),'pg_class')=
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.',
 'capture_body_sha256',(select encode(sha256(convert_to(btrim(replace(p.prosrc,E'\\r\\n',E'\\n'),E' \\t\\n\\r'),'UTF8')),'hex') from pg_proc p where p.oid=to_regprocedure('public.capture_staging_notification(text,uuid,jsonb)')),
 'capture_security',(select jsonb_build_object('owner',pg_get_userbyid(p.proowner),'definer',p.prosecdef,'settings',p.proconfig,
  'anon_execute',has_function_privilege('anon',p.oid,'EXECUTE'),'authenticated_execute',has_function_privilege('authenticated',p.oid,'EXECUTE'),
  'service_execute',has_function_privilege('service_role',p.oid,'EXECUTE')) from pg_proc p where p.oid=to_regprocedure('public.capture_staging_notification(text,uuid,jsonb)')),
 'allowlist_entries',(select count(*) from public.staging_registration_capture_allowlist),
 'allowlist_owner',(select pg_get_userbyid(relowner) from pg_class where oid='public.staging_registration_capture_allowlist'::regclass),
 'allowlist_rls',(select relrowsecurity from pg_class where oid='public.staging_registration_capture_allowlist'::regclass),
 'allowlist_columns',(select jsonb_agg(jsonb_build_object('name',attname,'type',atttypid::regtype::text,'not_null',attnotnull,'generated',attgenerated,'identity',attidentity) order by attnum)
  from pg_attribute where attrelid='public.staging_registration_capture_allowlist'::regclass and attnum>0 and not attisdropped),
 'allowlist_custom_triggers',(select count(*) from pg_trigger where tgrelid='public.staging_registration_capture_allowlist'::regclass and not tgisinternal),
 'allowlist_rules',(select count(*) from pg_rewrite where ev_class='public.staging_registration_capture_allowlist'::regclass),
 'allowlist_policies',(select count(*) from pg_policy where polrelid='public.staging_registration_capture_allowlist'::regclass),
 'no_client_table_access',not has_table_privilege('anon','public.staging_registration_capture_allowlist','SELECT,INSERT,UPDATE,DELETE') and not has_table_privilege('authenticated','public.staging_registration_capture_allowlist','SELECT,INSERT,UPDATE,DELETE'),
 'service_table_read_only',has_table_privilege('service_role','public.staging_registration_capture_allowlist','SELECT') and not has_table_privilege('service_role','public.staging_registration_capture_allowlist','INSERT,UPDATE,DELETE'),
 'identities',(select jsonb_agg(jsonb_build_object('test',w.n,'user_id',w.user_id,
  'auth_verified',exists(select 1 from auth.users u where u.id=w.user_id and u.email=w.email and u.email_confirmed_at is not null),
  'allowlisted',exists(select 1 from public.staging_registration_capture_allowlist a where a.user_id=w.user_id and a.registration_email=w.email and a.enabled),
  'original_choice',(select signup_opt_in_requested from public.newsletter_preferences where user_id=w.user_id),
  'current_consent',(select opted_in from public.newsletter_preferences where user_id=w.user_id),
  'signup_audits',(select count(*) from public.newsletter_consent_events where user_id=w.user_id and action='signup_request'),
  'verification_audits',(select count(*) from public.newsletter_consent_events where user_id=w.user_id and action='email_verified'),
  'withdrawal_audits',(select count(*) from public.newsletter_consent_events where user_id=w.user_id and action='preference_change' and choice is false),
  'pending_events',(select count(*) from public.registration_notification_events where user_id=w.user_id and state='pending'),
  'accepted_events',(select count(*) from public.registration_notification_events where user_id=w.user_id and state='accepted'),
  'receipts',(select count(*) from public.staging_notification_receipts r join public.registration_notification_events e on e.id=r.delivery_id where r.kind='registration_verified' and e.user_id=w.user_id)
 ) order by w.n) from wanted w),
 'all_pending_registration_events',(select count(*) from public.registration_notification_events where state='pending'),
 'survey_events',(select count(*) from public.survey_notification_events),
 'survey_receipts',(select count(*) from public.staging_notification_receipts where kind='survey'),
 'survey_capture_attempts',(select coalesce(sum(attempts),0) from public.staging_notification_receipts where kind='survey')
) as registration_extension_metadata;
"""
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
 for filename,text in [('011_registration_capture_extend.sql',install),('011_registration_capture_rollback.sql',rollback),('011_registration_capture_preflight_readonly.sql',query),('011_registration_capture_verify_readonly.sql',query)]:
  path=ROOT/'supabase/staging'/filename
  if args.check:
   if not path.exists() or path.read_text()!=text:raise SystemExit('Stale generated SQL: '+filename)
  else:path.write_text(text)
if __name__=='__main__':main()
