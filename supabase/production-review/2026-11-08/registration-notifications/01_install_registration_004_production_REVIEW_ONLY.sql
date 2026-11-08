-- DEVELOPMENT CANDIDATE. No cloud installation authorised by this file alone.
-- Server records signup intent, first Auth confirmation and later preferences.
-- No email/network calls in Auth triggers. No existing-user backfill or credit changes.
-- PREPARATION ONLY - DO NOT EXECUTE. Production project: arnzqizcycesukplmvuc.
-- Copy prepared from the reviewed 004 candidate; its underlying schema/function
-- definitions are unchanged. Requires separate approval and fresh preflight.
-- A textual project ID and acknowledgement are NOT independent project attestation.
-- The NOT_APPROVED value deliberately makes this file non-executable as supplied.
-- Stop if project identity, roles, baseline tables, existing objects, or Auth triggers drift.
begin;
set local lock_timeout = '5s';
set local statement_timeout = '60s';
set local urbanfold.production_registration_approval = 'NOT_APPROVED';
do $preflight$
declare n integer;
begin
 if current_setting('urbanfold.production_registration_approval',true)
    is distinct from 'APPROVED arnzqizcycesukplmvuc REGISTRATION 004 FRESH INSTALL'
 then raise exception 'Separate production installation approval not set; no changes permitted.'; end if;
 if current_user <> 'postgres' or auth.uid() is not null
    or auth.jwt()->>'role' is not null
 then raise exception 'Trusted postgres session without simulated JWT claims required.'; end if;
 if current_setting('server_version_num')::integer < 170000
 then raise exception 'Reviewed PostgreSQL 17+ baseline expected.'; end if;
 if to_regclass('auth.users') is null
 then raise exception 'Supabase Auth users table missing.'; end if;
 select count(*) into n from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
 where ns.nspname='public' and c.relname in
 ('properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos')
 and c.relkind='r' and c.relrowsecurity
 and pg_get_userbyid(c.relowner)='postgres';
 if n<>7 then raise exception 'Survey baseline table/owner/RLS mismatch; STOP.'; end if;
 if exists(select 1 from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
 where ns.nspname='public' and c.relname in
 ('newsletter_preferences','newsletter_consent_events','registration_notification_events'))
 or exists(select 1 from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
 where ns.nspname='public' and p.proname in
 ('record_auth_registration','get_newsletter_preference','set_newsletter_preference',
 'claim_registration_notification','finish_registration_notification','recover_stale_registration_notifications'))
 or exists(select 1 from pg_trigger t where t.tgrelid='auth.users'::regclass
 and t.tgname in ('urbanfold_auth_signup','urbanfold_auth_first_confirmation'))
 then raise exception 'Existing registration objects found; fresh installer cannot run.'; end if;
end
$preflight$;
create table if not exists public.newsletter_preferences(
 user_id uuid primary key references auth.users(id) on delete cascade,
 signup_opt_in_requested boolean,
 opted_in boolean not null default false,
 verified_at timestamptz,
 consent_version text not null default '2026-10-23',
 updated_at timestamptz not null default clock_timestamp()
);
create table if not exists public.newsletter_consent_events(
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 choice boolean,
 action text not null check(action in('signup_request','email_verified','preference_change')),
 source text not null,
 consent_version text not null,
 consent_text text not null,
 occurred_at timestamptz not null default clock_timestamp()
);
create index if not exists newsletter_consent_user_time on public.newsletter_consent_events(user_id,occurred_at);
create table if not exists public.registration_notification_events(
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null unique references auth.users(id) on delete cascade,
 registration_email text not null,
 registered_at timestamptz not null,
 verified_at timestamptz not null,
 newsletter_signup_choice boolean,
 newsletter_opted_in_at_verification boolean not null,
 state text not null default 'pending' check(state in('pending','sending','accepted','uncertain')),
 created_at timestamptz not null default clock_timestamp(),
 finished_at timestamptz,
 claim_started_at timestamptz,
 completion_reason text
);
-- Support reapplying the candidate after a separately reviewed early-004 install.
alter table public.registration_notification_events add column if not exists claim_started_at timestamptz;
alter table public.registration_notification_events add column if not exists completion_reason text;
-- Legacy attempts have unknown claim times. Count them conservatively from this
-- migration, rather than exempting them from the new rolling limits.
update public.registration_notification_events set claim_started_at=clock_timestamp()
 where state<>'pending' and claim_started_at is null;
create index if not exists registration_notification_pending on public.registration_notification_events(created_at) where state='pending';
create index if not exists registration_notification_claim_time on public.registration_notification_events(claim_started_at)
 where claim_started_at is not null;
alter table public.newsletter_preferences enable row level security;
alter table public.newsletter_consent_events enable row level security;
alter table public.registration_notification_events enable row level security;
revoke all on public.newsletter_preferences,public.newsletter_consent_events,public.registration_notification_events from public,anon,authenticated;
grant select on public.newsletter_preferences,public.newsletter_consent_events to authenticated;
grant all on public.newsletter_preferences,public.registration_notification_events to service_role;
revoke all on public.newsletter_consent_events from service_role;
grant select on public.newsletter_consent_events to service_role;
drop policy if exists newsletter_preferences_own on public.newsletter_preferences;
create policy newsletter_preferences_own on public.newsletter_preferences for select to authenticated using(user_id=(select auth.uid()));
drop policy if exists newsletter_consent_own on public.newsletter_consent_events;
create policy newsletter_consent_own on public.newsletter_consent_events for select to authenticated using(user_id=(select auth.uid()));

create or replace function public.record_auth_registration()
returns trigger language plpgsql security definer set search_path='' as $$
declare requested boolean;prefs public.newsletter_preferences;
 wording constant text:='Email me Urbanfold newsletters and updates (optional)';
begin
 if tg_op='INSERT' then
  requested:=case when jsonb_typeof(new.raw_user_meta_data->'newsletter_subscribed')='boolean'
    then (new.raw_user_meta_data->>'newsletter_subscribed')::boolean else false end;
  insert into public.newsletter_preferences(user_id,signup_opt_in_requested) values(new.id,requested) on conflict(user_id) do nothing;
  insert into public.newsletter_consent_events(user_id,choice,action,source,consent_version,consent_text)
  values(new.id,requested,'signup_request','auth_signup_metadata_intent','2026-10-23',wording);
 end if;
 if new.email_confirmed_at is null then return new;end if;
 if tg_op='UPDATE' then
  if old.email_confirmed_at is not null then return new;end if;
  -- Do not enqueue historical accounts or infer their original checkbox after feature installation.
  if not exists(select 1 from public.newsletter_preferences where user_id=new.id and signup_opt_in_requested is not null) then return new;end if;
 end if;
 -- Only signup intent captured at account insertion is eligible; never trust later mutable metadata.
 insert into public.newsletter_preferences(user_id) values(new.id) on conflict(user_id) do nothing;
 select * into prefs from public.newsletter_preferences where user_id=new.id for update;
 update public.newsletter_preferences set verified_at=new.email_confirmed_at,
  opted_in=coalesce(prefs.signup_opt_in_requested,false),updated_at=clock_timestamp() where user_id=new.id and verified_at is null;
 -- A user can produce only one first-confirmation notification. Email changes/reconfirmation do not resend.
 insert into public.registration_notification_events(user_id,registration_email,registered_at,verified_at,
  newsletter_signup_choice,newsletter_opted_in_at_verification)
 values(new.id,new.email,new.created_at,new.email_confirmed_at,prefs.signup_opt_in_requested,coalesce(prefs.signup_opt_in_requested,false))
 on conflict(user_id) do nothing;
 if found then
  insert into public.newsletter_consent_events(user_id,choice,action,source,consent_version,consent_text)
  values(new.id,prefs.signup_opt_in_requested,'email_verified','auth_first_confirmation','2026-10-23',wording);
 end if;
 return new;
end $$;
revoke all on function public.record_auth_registration() from public,anon,authenticated;
drop trigger if exists urbanfold_auth_signup on auth.users;
create trigger urbanfold_auth_signup after insert on auth.users for each row execute function public.record_auth_registration();
drop trigger if exists urbanfold_auth_first_confirmation on auth.users;
create trigger urbanfold_auth_first_confirmation after update of email_confirmed_at on auth.users for each row execute function public.record_auth_registration();

create or replace function public.get_newsletter_preference()
returns jsonb language plpgsql security definer set search_path='' as $$
declare person uuid:=auth.uid();prefs public.newsletter_preferences;
begin
 if person is null then raise exception 'Sign in to view newsletter preferences.' using errcode='42501';end if;
 select * into prefs from public.newsletter_preferences where user_id=person;
 return jsonb_build_object('opted_in',coalesce(prefs.opted_in,false),'recorded',prefs.user_id is not null,'consent_version','2026-10-23');
end $$;
create or replace function public.set_newsletter_preference(subscribe boolean)
returns jsonb language plpgsql security definer set search_path='' as $$
declare person uuid:=auth.uid();previous boolean;created uuid;
begin
 if person is null or subscribe is null or not exists(select 1 from auth.users where id=person and email_confirmed_at is not null) then
  raise exception 'A verified account and explicit preference are required.' using errcode='42501';end if;
 -- Serialise preference creation/updates, never allow a caller-supplied user ID or timestamp.
 perform 1 from auth.users where id=person for update;
 insert into public.newsletter_preferences(user_id,verified_at) select person,email_confirmed_at from auth.users where id=person on conflict(user_id) do nothing returning user_id into created;
 select opted_in into previous from public.newsletter_preferences where user_id=person for update;
 if created is not null or previous is distinct from subscribe then
  update public.newsletter_preferences set opted_in=subscribe,updated_at=clock_timestamp() where user_id=person;
  insert into public.newsletter_consent_events(user_id,choice,action,source,consent_version,consent_text)
  values(person,subscribe,'preference_change','authenticated_preference_form','2026-10-23','Email me Urbanfold newsletters and updates (optional)');
 end if;
 return public.get_newsletter_preference();
end $$;
revoke all on function public.get_newsletter_preference() from public,anon;
revoke all on function public.set_newsletter_preference(boolean) from public,anon;
grant execute on function public.get_newsletter_preference(),public.set_newsletter_preference(boolean) to authenticated;

-- Five minutes exceeds the worker's bounded transport/finish waits. Interrupted
-- attempts are ambiguous, never safe to automatically requeue or resend.
create or replace function public.recover_stale_registration_notifications()
returns integer language plpgsql security definer set search_path='' as $$
declare recovered integer;
begin
 perform pg_advisory_xact_lock(hashtextextended('urbanfold.registration.dispatch',0));
 update public.registration_notification_events
 set state='uncertain',finished_at=clock_timestamp(),completion_reason='worker_interrupted'
 where state='sending' and (claim_started_at is null or claim_started_at<=clock_timestamp()-interval '5 minutes');
 get diagnostics recovered=row_count;
 return recovered;
end $$;
revoke all on function public.recover_stale_registration_notifications() from public,anon,authenticated;
grant execute on function public.recover_stale_registration_notifications() to service_role;

create or replace function public.claim_registration_notification()
returns jsonb language plpgsql security definer set search_path='' as $$
declare e public.registration_notification_events; claimed_at timestamptz;
 minute_count integer;hour_count integer;retry_seconds integer:=1;next_slot timestamptz;
begin
 -- Serialize ALL callers across rows: SKIP LOCKED alone cannot enforce a global cap.
 perform pg_advisory_xact_lock(hashtextextended('urbanfold.registration.dispatch',0));
 perform public.recover_stale_registration_notifications();
 select * into e from public.registration_notification_events where state='pending' order by created_at,id for update skip locked limit 1;
 if not found then return null;end if;
 claimed_at:=clock_timestamp();
 select count(*) filter(where claim_started_at>claimed_at-interval '1 minute'),count(*)
 into minute_count,hour_count from public.registration_notification_events
 where claim_started_at>claimed_at-interval '1 hour';
 if minute_count>=5 then
  select claim_started_at+interval '1 minute' into next_slot
  from public.registration_notification_events where claim_started_at>claimed_at-interval '1 minute'
  order by claim_started_at offset (minute_count-5) limit 1;
  retry_seconds:=greatest(retry_seconds,ceil(extract(epoch from next_slot-claimed_at))::integer);
 end if;
 if hour_count>=50 then
  select claim_started_at+interval '1 hour' into next_slot
  from public.registration_notification_events where claim_started_at>claimed_at-interval '1 hour'
  order by claim_started_at offset (hour_count-50) limit 1;
  retry_seconds:=greatest(retry_seconds,ceil(extract(epoch from next_slot-claimed_at))::integer);
 end if;
 if minute_count>=5 or hour_count>=50 then
  return jsonb_build_object('status','rate_limited','retry_after_seconds',retry_seconds);
 end if;
 update public.registration_notification_events set state='sending',claim_started_at=claimed_at,
  finished_at=null,completion_reason=null where id=e.id;
 return jsonb_build_object('id',e.id,'claim_started_at',claimed_at,'user_id',e.user_id,'registration_email',e.registration_email,
  'registered_at',e.registered_at,'verified_at',e.verified_at,'newsletter_signup_choice',e.newsletter_signup_choice,
  'newsletter_opted_in_at_verification',e.newsletter_opted_in_at_verification);
end $$;
create or replace function public.finish_registration_notification(event uuid,accepted boolean)
returns void language plpgsql security definer set search_path='' as $$
begin
 update public.registration_notification_events set state=case when accepted then 'accepted' else 'uncertain' end,
 finished_at=clock_timestamp(),completion_reason=case when accepted then 'transport_accepted' else 'transport_uncertain' end
 where id=event and state='sending';
end $$;
-- New workers finish against their exact claim and inspect the persisted state.
-- A delayed worker cannot turn an already recovered/uncertain attempt accepted.
-- Keep the two-argument early-candidate RPC for migration compatibility only.
create or replace function public.finish_registration_notification(event uuid,accepted boolean,claimed_at timestamptz)
returns jsonb language plpgsql security definer set search_path='' as $$
declare persisted_state text;
begin
 update public.registration_notification_events e
 set state=case when accepted then 'accepted' else 'uncertain' end,
 finished_at=clock_timestamp(),completion_reason=case when accepted then 'transport_accepted' else 'transport_uncertain' end
 where e.id=event and e.state='sending' and e.claim_started_at=claimed_at;
 select e.state into persisted_state from public.registration_notification_events e where e.id=event;
 return jsonb_build_object('state',coalesce(persisted_state,'uncertain'));
end $$;
revoke all on function public.claim_registration_notification(),public.finish_registration_notification(uuid,boolean) from public,anon,authenticated;
grant execute on function public.claim_registration_notification(),public.finish_registration_notification(uuid,boolean) to service_role;
revoke all on function public.finish_registration_notification(uuid,boolean,timestamptz) from public,anon,authenticated;
grant execute on function public.finish_registration_notification(uuid,boolean,timestamptz) to service_role;
commit;
