-- REVIEW ONLY, separate execution approval required. Production arnzqizcycesukplmvuc.
-- No secrets or customer rows in this file. Acknowledgements do NOT prove connection identity.
-- Run ONLY after approved Cron installation. SELECT-only: never invokes the job.
select jobid,jobname,schedule,active,
 command like '%https://arnzqizcycesukplmvuc.supabase.co/functions/v1/dispatch-registration-notifications%' as correct_production_endpoint,
 command like '%urbanfold_production_registration_dispatch%' as dispatch_vault_reference,
 command like '%urbanfold_production_public_key%' as public_key_vault_reference
from cron.job where jobname='urbanfold-production-verified-registration';
-- Do not return Vault decrypted_secret, full job commands, HTTP headers or worker payloads.
