-- PREPARED ROLLBACK/PAUSE ONLY. Changes Auth behaviour: separate approval required.
-- Verify project hexhtduvqzleoazusskh. Pause dispatcher/scheduler separately first.
-- Preserve all consent/queue/receipt data; no DROP/DELETE/reset or credit changes.
-- Review that these two trigger names are the newly installed 004 triggers.
-- Use a new SQL Editor session; do not run while a failed transaction is open.
begin;
-- After explicit approval only, uncomment this acknowledgement:
-- set local urbanfold.registration_rollback_approved='yes';
do $$ begin
 if current_user<>'postgres' or auth.uid() is not null or auth.jwt()->>'role' is not null
 or current_setting('urbanfold.registration_rollback_approved',true) is distinct from 'yes' then
  raise exception 'Explicit approved staging rollback acknowledgement required.';
 end if;
 if obj_description(to_regclass('public.properties'),'pg_class') is distinct from
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.' then
  raise exception 'Staging baseline required. Verify project hexhtduvqzleoazusskh.';
 end if;
 if (select count(*) from pg_trigger where tgrelid='auth.users'::regclass
   and tgname in('urbanfold_auth_signup','urbanfold_auth_first_confirmation'))<>2 then
  raise exception 'Expected two registration triggers; stop and review current metadata.';
 end if;
end $$;
alter table auth.users disable trigger urbanfold_auth_signup;
alter table auth.users disable trigger urbanfold_auth_first_confirmation;
commit;
-- Accounts created during the pause have unrecorded signup choice. Do not backfill
-- newsletter consent from mutable metadata or automatically send historic notices.
-- Re-enable only after reviewed cause/fix/metadata and separate approval.
