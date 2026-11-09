-- PREPARED EMERGENCY PAUSE ONLY. NOT APPROVED; do not run routinely.
-- PRODUCTION arnzqizcycesukplmvuc. Separately authorise this named action.
-- Pauses ONLY the two newly installed 004 Auth triggers. Keeps customer data,
-- existing verification/recovery configuration and consent/queue evidence.
-- Review actual trigger definitions before any use. NO AUTOMATIC ROLLBACK.
begin;
set local lock_timeout='5s';
set local statement_timeout='30s';
set local urbanfold.production_trigger_pause_approval='NOT_APPROVED';
do $pause$
declare target_count integer;
begin
 if current_setting('urbanfold.production_trigger_pause_approval',true)
    is distinct from 'APPROVED arnzqizcycesukplmvuc PAUSE EXACT 004 AUTH TRIGGERS'
 then raise exception 'Explicit separate production pause approval required.';end if;
 if current_user<>'postgres' or auth.uid() is not null or auth.jwt()->>'role' is not null
 then raise exception 'Trusted postgres session without simulated JWT claims required.';end if;
 select count(*) into target_count from pg_trigger t
 where t.tgrelid='auth.users'::regclass
 and t.tgname in ('urbanfold_auth_signup','urbanfold_auth_first_confirmation')
 and not t.tgisinternal and t.tgenabled='O'
 and t.tgfoid=to_regprocedure('public.record_auth_registration()');
 if target_count<>2 then raise exception 'Two exact enabled Auth triggers not found; STOP.';end if;
 if not exists(select 1 from pg_proc p
 where p.oid=to_regprocedure('public.record_auth_registration()')
 and pg_get_userbyid(p.proowner)='postgres' and p.prosecdef
 and encode(sha256(convert_to(replace(p.prosrc,E'\r\n',E'\n'),'UTF8')),'hex')
 ='0334f6287816922e1cd6daf79fefa0fd59d11ca42608e7bc6171465975cf7fc0')
 then raise exception 'Original reviewed registration function changed; STOP.';end if;
end
$pause$;
alter table auth.users disable trigger urbanfold_auth_signup;
alter table auth.users disable trigger urbanfold_auth_first_confirmation;
commit;
-- Accounts created or verified while paused may lack captured consent intent.
-- Do not backfill mutable metadata or automatically resend registrations.
