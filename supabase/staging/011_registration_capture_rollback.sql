-- PROPOSAL ONLY: row-only rollback (disable added pairs, preserve evidence) of EXISTING010, staging hexhtduvqzleoazusskh.
-- Separate SQL approval required. No function/schema/policy/secret changes or sends.
-- Pause/avoid automatic dispatcher invocations before approval; never run010 again.
begin;
set local search_path=pg_catalog;
do $$
declare first_before jsonb;first_after jsonb;data_before jsonb;data_after jsonb;
begin

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
  and exists(select 1 from unnest(p.proconfig) s where s in('search_path=""','search_path='))
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
 if not exists(select 1 from public.staging_registration_capture_allowlist where user_id='b83f87d8-abf2-4800-beab-8279917804c7'::uuid
  and registration_email='urbanfolduk+staging-reg-01@gmail.com' and enabled) then
  raise exception 'Test1 exact enabled entry missing or changed; never overwrite it.';
 end if;

 if (select count(*) from public.staging_registration_capture_allowlist)<>3
 or (select count(*) from (values (1,'b83f87d8-abf2-4800-beab-8279917804c7'::uuid,'urbanfolduk+staging-reg-01@gmail.com'::text),
 (2,'d2598ebf-d44c-4e11-81a5-d82f3d06ada1'::uuid,'urbanfolduk+staging-reg-02@gmail.com'::text),
 (3,'3a4e8d72-bf58-468a-b24f-0417c4a64f5b'::uuid,'urbanfolduk+staging-reg-03@gmail.com'::text)) wanted(n,user_id,email)
  join public.staging_registration_capture_allowlist a on a.user_id=wanted.user_id and a.registration_email=wanted.email where wanted.n in(2,3))<>2 then
  raise exception 'Expected exact three-entry allowlist. Stop; never modify unknown entries.';
 end if;
 select to_jsonb(a) into first_before from public.staging_registration_capture_allowlist a where user_id='b83f87d8-abf2-4800-beab-8279917804c7'::uuid;
 select jsonb_build_object(
 'registration_events',(select coalesce(jsonb_agg(to_jsonb(t) order by t.id),'[]'::jsonb) from public.registration_notification_events t),
 'receipts',(select coalesce(jsonb_agg(to_jsonb(t) order by t.kind,t.delivery_id),'[]'::jsonb) from public.staging_notification_receipts t),
 'preferences',(select coalesce(jsonb_agg(to_jsonb(t) order by t.user_id),'[]'::jsonb) from public.newsletter_preferences t),
 'consent_audit',(select coalesce(jsonb_agg(to_jsonb(t) order by t.id),'[]'::jsonb) from public.newsletter_consent_events t),
 'survey_events',(select coalesce(jsonb_agg(to_jsonb(t) order by t.id),'[]'::jsonb) from public.survey_notification_events t),
 'free_allocations',(select coalesce(jsonb_agg(to_jsonb(t) order by t.user_id),'[]'::jsonb) from public.survey_free_allocations t),
 'purchases',(select coalesce(jsonb_agg(to_jsonb(t) order by t.checkout_session_id),'[]'::jsonb) from public.survey_credit_purchases t),
 'revocations',(select coalesce(jsonb_agg(to_jsonb(t) order by t.payment_intent_id),'[]'::jsonb) from public.survey_credit_revocations t)
) into data_before;
 update public.staging_registration_capture_allowlist set enabled=false
 where (user_id,registration_email) in (select user_id,email from (values (1,'b83f87d8-abf2-4800-beab-8279917804c7'::uuid,'urbanfolduk+staging-reg-01@gmail.com'::text),
 (2,'d2598ebf-d44c-4e11-81a5-d82f3d06ada1'::uuid,'urbanfolduk+staging-reg-02@gmail.com'::text),
 (3,'3a4e8d72-bf58-468a-b24f-0417c4a64f5b'::uuid,'urbanfolduk+staging-reg-03@gmail.com'::text)) wanted(n,user_id,email) where n in(2,3))
 and enabled;
 select to_jsonb(a) into first_after from public.staging_registration_capture_allowlist a where user_id='b83f87d8-abf2-4800-beab-8279917804c7'::uuid;
 select jsonb_build_object(
 'registration_events',(select coalesce(jsonb_agg(to_jsonb(t) order by t.id),'[]'::jsonb) from public.registration_notification_events t),
 'receipts',(select coalesce(jsonb_agg(to_jsonb(t) order by t.kind,t.delivery_id),'[]'::jsonb) from public.staging_notification_receipts t),
 'preferences',(select coalesce(jsonb_agg(to_jsonb(t) order by t.user_id),'[]'::jsonb) from public.newsletter_preferences t),
 'consent_audit',(select coalesce(jsonb_agg(to_jsonb(t) order by t.id),'[]'::jsonb) from public.newsletter_consent_events t),
 'survey_events',(select coalesce(jsonb_agg(to_jsonb(t) order by t.id),'[]'::jsonb) from public.survey_notification_events t),
 'free_allocations',(select coalesce(jsonb_agg(to_jsonb(t) order by t.user_id),'[]'::jsonb) from public.survey_free_allocations t),
 'purchases',(select coalesce(jsonb_agg(to_jsonb(t) order by t.checkout_session_id),'[]'::jsonb) from public.survey_credit_purchases t),
 'revocations',(select coalesce(jsonb_agg(to_jsonb(t) order by t.payment_intent_id),'[]'::jsonb) from public.survey_credit_revocations t)
) into data_after;
 if first_before is distinct from first_after or data_before is distinct from data_after then
  raise exception 'Test1/history/consent/credit data changed unexpectedly; rollback this transaction.';
 end if;
end $$;
commit;
-- Both added rows retained disabled. Re-enable requires separate approval; no reset/reinstall.
