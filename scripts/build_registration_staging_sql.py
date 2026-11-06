"""Generate a fresh-project-only staging wrapper; never execute SQL."""
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parents[1]
GUARD="""
do $$ begin
 if current_user <> 'postgres' or auth.uid() is not null or auth.jwt()->>'role' is not null then
  raise exception 'Staging postgres SQL session without JWT claims required.';
 end if;
 if obj_description(to_regclass('public.properties'),'pg_class') is distinct from
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.' then
  raise exception 'Reviewed staging baseline required. Verify project hexhtduvqzleoazusskh.';
 end if;
 if exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace
   where n.nspname='public' and c.relname in
   ('newsletter_preferences','newsletter_consent_events','registration_notification_events'))
 or exists(select 1 from pg_trigger where tgrelid='auth.users'::regclass
   and tgname in ('urbanfold_auth_signup','urbanfold_auth_first_confirmation'))
 or exists(select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname in
   ('record_auth_registration','get_newsletter_preference','set_newsletter_preference',
   'claim_registration_notification','finish_registration_notification','recover_stale_registration_notifications')) then
  raise exception 'Registration objects already exist. STOP and review an upgrade; do not rerun the fresh installer.';
 end if;
end $$;
"""
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
 source=(ROOT/'supabase/004_verified_registration_notifications.sql').read_text()
 text=('-- GENERATED FRESH STAGING INSTALLER. No SQL executed by generation.\n'
       '-- Verify Dashboard project hexhtduvqzleoazusskh. Guards are not independent project attestation.\n'
       '-- Run only after metadata preflight and separate installation approval.\n'
       +source.replace('begin;','begin;\n'+GUARD,1))
 out=ROOT/'supabase/staging/004_registration_install_fresh.sql'
 if args.check:
  if not out.exists() or out.read_text()!=text:raise SystemExit('Stale staging 004 installer')
 else:out.write_text(text)
if __name__=='__main__':main()
