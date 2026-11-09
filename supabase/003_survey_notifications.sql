-- PROPOSED F02 migration. Not applied to production. Apply only after approval.
-- Additive notification bookkeeping; no changes to surveys, photos or £6 credits.
begin;
create table if not exists public.survey_notification_events (
 id uuid primary key default gen_random_uuid(),
 property_id uuid not null references public.properties(id) on delete cascade,
 actor_id uuid not null references auth.users(id) on delete cascade,
 submission_at timestamptz not null,
 content_fingerprint text not null check(content_fingerprint ~ '^[0-9a-f]{64}$'),
 state text not null default 'sending' check(state in ('sending','accepted','uncertain')),
 created_at timestamptz not null default now(),
 finished_at timestamptz,
 unique(property_id,submission_at),
 unique(property_id,content_fingerprint)
);
create index if not exists survey_notification_actor_time on public.survey_notification_events(actor_id,created_at);
alter table public.survey_notification_events enable row level security;
revoke all on public.survey_notification_events from public,anon,authenticated;
grant all on public.survey_notification_events to service_role;

-- Actor comes from verified Auth on the server, never from a browser body.
create or replace function public.claim_survey_notification(actor uuid, property uuid, revision timestamptz)
returns jsonb language plpgsql security definer set search_path='' as $$
declare
 p public.properties;
 e public.survey_notification_events;
 actor_email text;
 confirmed timestamptz;
 fingerprint text;
begin
 select email,email_confirmed_at into actor_email,confirmed from auth.users where id=actor;
 if actor_email is null or confirmed is null then raise exception 'NOTIFICATION_AUTH_REQUIRED' using errcode='42501'; end if;
 -- Serialise rolling actor caps across properties, then per-property claims.
 perform pg_advisory_xact_lock(hashtextextended(actor::text,0));
 select * into p from public.properties where id=property for update;
 if not found or (p.user_id is distinct from actor and actor_email <> 'urbanfolduk@gmail.com') then
  raise exception 'NOTIFICATION_NOT_ALLOWED' using errcode='42501';
 end if;
 if p.last_submitted_at is null or p.last_submitted_at is distinct from revision then
  raise exception 'NOTIFICATION_SUBMISSION_CHANGED';
 end if;
 -- Deduplicate unchanged content even when an owner presses Submit again and
 -- the completion timestamp changes. Signing URLs are not persisted or hashed.
 select encode(sha256(convert_to(jsonb_build_object(
  'property',to_jsonb(p)-'last_submitted_at'-'address_locked'-'created_at'-'status',
  'extensions',(select coalesce(jsonb_agg(to_jsonb(x)-'created_at' order by x.id),'[]'::jsonb) from public.extensions x where x.property_id=property),
  'rooms',(select coalesce(jsonb_agg(to_jsonb(x)-'created_at' order by x.id),'[]'::jsonb) from public.rooms x where x.property_id=property),
  'exterior',(select coalesce(jsonb_agg(to_jsonb(x)-'created_at' order by x.id),'[]'::jsonb) from public.exterior_photos x where x.property_id=property),
  'extension_photos',(select coalesce(jsonb_agg(to_jsonb(x)-'created_at' order by x.id),'[]'::jsonb) from public.extension_photos x where x.property_id=property),
  'sketches',(select coalesce(jsonb_agg(to_jsonb(x)-'created_at' order by x.id),'[]'::jsonb) from public.sketch_photos x where x.property_id=property),
  'room_photos',(select coalesce(jsonb_agg(to_jsonb(x)-'created_at' order by x.id),'[]'::jsonb) from public.room_photos x join public.rooms r on r.id=x.room_id where r.property_id=property)
 )::text,'UTF8')),'hex') into fingerprint;
 select * into e from public.survey_notification_events where property_id=property and content_fingerprint=fingerprint;
 if found then return jsonb_build_object('id',e.id,'state',e.state,'claimed',false); end if;
 if (select count(*) from public.survey_notification_events where actor_id=actor and created_at>now()-interval '24 hours')>=20
    or (select count(*) from public.survey_notification_events where property_id=property and created_at>now()-interval '24 hours')>=5 then
  raise exception 'NOTIFICATION_RATE_LIMIT';
 end if;
 if coalesce(trim(p.client_email),'') !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$' then
  raise exception 'NOTIFICATION_RECIPIENT_INVALID';
 end if;
 insert into public.survey_notification_events(property_id,actor_id,submission_at,content_fingerprint)
 values(property,actor,revision,fingerprint) returning * into e;
 return jsonb_build_object('id',e.id,'state',e.state,'claimed',true,
  'payload',jsonb_build_object('property_id',p.id,'client_email',trim(p.client_email),
   'address',p.address,'surveyor_name',p.surveyor_name));
end $$;
revoke all on function public.claim_survey_notification(uuid,uuid,timestamptz) from public,anon,authenticated;
grant execute on function public.claim_survey_notification(uuid,uuid,timestamptz) to service_role;

create or replace function public.finish_survey_notification(event uuid, accepted boolean)
returns void language plpgsql security definer set search_path='' as $$
begin
 update public.survey_notification_events set state=case when accepted then 'accepted' else 'uncertain' end,finished_at=now()
 where id=event and state='sending';
end $$;
revoke all on function public.finish_survey_notification(uuid,boolean) from public,anon,authenticated;
grant execute on function public.finish_survey_notification(uuid,boolean) to service_role;
commit;
