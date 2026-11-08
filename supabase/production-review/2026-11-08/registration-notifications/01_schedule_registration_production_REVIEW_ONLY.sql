-- URBANFOLD PRODUCTION SCHEDULER CANDIDATE - PREPARATION ONLY.
-- Target: Urbanfold-Survey / arnzqizcycesukplmvuc.
-- DO NOT RUN without separate, explicit approval for production scheduling.
-- This file does not enable pg_cron or pg_net, add Vault secrets, or modify Edge secrets.
-- A scheduler repeatedly calls a live endpoint. Keep transport disabled until
-- standalone authorization and controlled new-registration validation succeed.
begin;
set local lock_timeout='5s';
set local statement_timeout='30s';
set local urbanfold.registration_scheduler_approval='NOT_APPROVED';
do $preflight$
declare job_count integer;
begin
 if current_setting('urbanfold.registration_scheduler_approval',true)
   is distinct from 'APPROVED arnzqizcycesukplmvuc REGISTRATION CRON 1 MIN'
 then raise exception 'Production scheduler approval absent. No changes allowed.'; end if;
 if current_user<>'postgres' or auth.uid() is not null
    or auth.jwt()->>'role' is not null
 then raise exception 'Trusted postgres session without Auth JWT required.'; end if;
 if to_regclass('cron.job') is null
    or to_regclass('vault.decrypted_secrets') is null
    or to_regprocedure('net.http_post(text,jsonb,jsonb,jsonb,integer)') is null
 then raise exception 'Required extensions not installed/available; STOP.'; end if;
 if (select count(*) from pg_trigger where tgrelid='auth.users'::regclass
 and tgname in('urbanfold_auth_signup','urbanfold_auth_first_confirmation')
 and tgenabled='O')<>2
 then raise exception 'Registration triggers not enabled; STOP.'; end if;
 if (select count(*) from vault.decrypted_secrets
 where name in ('urbanfold_production_registration_dispatch',
                 'urbanfold_production_public_key'))<>2
 then raise exception 'Two separately approved Vault credentials required; STOP.'; end if;
 -- Prevent silently replacing an existing job or creating a duplicate.
 select count(*) into job_count from cron.job
 where jobname='urbanfold-production-verified-registration';
 if job_count<>0 then raise exception 'Registration scheduler job already exists; STOP.'; end if;
end
$preflight$;
-- Uses Vault at execution time; the private dispatch secret is never embedded
-- in the cron.job command or source repository.
select cron.schedule(
 'urbanfold-production-verified-registration',
 '* * * * *',
 $job$
 select net.http_post(
  url:='https://arnzqizcycesukplmvuc.supabase.co/functions/v1/dispatch-registration-notifications',
  headers:=jsonb_build_object(
   'Content-Type','application/json',
   'apikey',(select decrypted_secret from vault.decrypted_secrets
              where name='urbanfold_production_public_key'),
   'Authorization','Bearer '||(select decrypted_secret from vault.decrypted_secrets
              where name='urbanfold_production_registration_dispatch')
  ),
  body:='{}'::jsonb,
  timeout_milliseconds:=15000
 );
 $job$
);
commit;
-- Explicit halt after separate approval: SELECT cron.unschedule('urbanfold-production-verified-registration');
-- Disabling REGISTRATION_NOTIFICATION_TRANSPORT independently stops outgoing delivery.
