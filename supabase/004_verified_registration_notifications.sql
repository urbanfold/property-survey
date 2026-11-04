-- DEVELOPMENT CANDIDATE. No cloud installation authorised by this file alone.
-- Server records signup intent, first Auth confirmation and later preferences.
-- No email/network calls in Auth triggers. No existing-user backfill or credit changes.
begin;
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
 finished_at timestamptz
);
create index if not exists registration_notification_pending on public.registration_notification_events(created_at) where state='pending';
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

create or replace function public.claim_registration_notification()
returns jsonb language plpgsql security definer set search_path='' as $$
declare e public.registration_notification_events;
begin
 select * into e from public.registration_notification_events where state='pending' order by created_at,id for update skip locked limit 1;
 if not found then return null;end if;
 update public.registration_notification_events set state='sending' where id=e.id;
 return jsonb_build_object('id',e.id,'user_id',e.user_id,'registration_email',e.registration_email,
  'registered_at',e.registered_at,'verified_at',e.verified_at,'newsletter_signup_choice',e.newsletter_signup_choice,
  'newsletter_opted_in_at_verification',e.newsletter_opted_in_at_verification);
end $$;
create or replace function public.finish_registration_notification(event uuid,accepted boolean)
returns void language plpgsql security definer set search_path='' as $$
begin
 update public.registration_notification_events set state=case when accepted then 'accepted' else 'uncertain' end,
 finished_at=clock_timestamp() where id=event and state='sending';
end $$;
revoke all on function public.claim_registration_notification(),public.finish_registration_notification(uuid,boolean) from public,anon,authenticated;
grant execute on function public.claim_registration_notification(),public.finish_registration_notification(uuid,boolean) to service_role;
commit;
