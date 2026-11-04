-- OPTIONAL STAGING SCHEDULER TEMPLATE. NOT EXECUTED. Review after function tests.
-- No secret values in this SQL. Vault entries must be provisioned separately.
-- Never run this on production or enable a real email transport in staging.
begin;
do $$ begin
 if obj_description('public.properties'::regclass,'pg_class') is distinct from
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.' then raise exception 'STAGING_REQUIRED';end if;
 if to_regclass('cron.job') is null or to_regclass('vault.decrypted_secrets') is null
 or to_regprocedure('net.http_post(text,jsonb,jsonb,jsonb,integer)') is null then
  raise exception 'Review/enable staging Cron, pg_net and Vault before scheduling.';
 end if;
 if not exists(select 1 from vault.decrypted_secrets where name='urbanfold_staging_registration_dispatch')
 or not exists(select 1 from vault.decrypted_secrets where name='urbanfold_staging_public_key') then
  raise exception 'Required staging-only Vault entries are not configured.';
 end if;
end $$;
-- One pending verified registration per minute; accepted/uncertain events are not reclaimed.
select cron.schedule('urbanfold-staging-verified-registration','* * * * *',$job$
 select net.http_post(
  url:='https://hexhtduvqzleoazusskh.supabase.co/functions/v1/dispatch-registration-notifications',
  headers:=jsonb_build_object('Content-Type','application/json',
   'apikey',(select decrypted_secret from vault.decrypted_secrets where name='urbanfold_staging_public_key'),
   'Authorization','Bearer '||(select decrypted_secret from vault.decrypted_secrets where name='urbanfold_staging_registration_dispatch')),
  body:='{}'::jsonb,timeout_milliseconds:=15000
 );
$job$);
commit;
