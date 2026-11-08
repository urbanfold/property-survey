-- F02 BREVO DUAL-RECIPIENT DELIVERY LEDGER - DEVELOPMENT CANDIDATE ONLY.
-- Additive to previously reviewed 003 survey notifications; no production approval.
-- No database trigger sends emails; all network calls remain in verified gateway.
begin;
create table if not exists public.survey_notification_deliveries(
 event_id uuid not null references public.survey_notification_events(id) on delete cascade,
 recipient_kind text not null check(recipient_kind in ('admin','customer')),
 state text not null default 'sending' check(state in('sending','accepted','uncertain')),
 created_at timestamptz not null default clock_timestamp(),
 finished_at timestamptz,
 primary key(event_id,recipient_kind)
);
alter table public.survey_notification_deliveries enable row level security;
revoke all on public.survey_notification_deliveries from public,anon,authenticated;
grant select on public.survey_notification_deliveries to service_role;
-- The handler calls this before contacting Brevo. Both rows must be created
-- before either email may be sent. A duplicate/uncertain event is not reclaimed.
create or replace function public.prepare_survey_brevo_deliveries(event uuid)
returns boolean language plpgsql security definer set search_path='' as $$
declare current_state text; existing integer;
begin
 select state into current_state from public.survey_notification_events where id=event for update;
 if current_state is distinct from 'sending' then return false; end if;
 select count(*) into existing from public.survey_notification_deliveries where event_id=event;
 if existing<>0 then return false; end if;
 insert into public.survey_notification_deliveries(event_id,recipient_kind)
 values (event,'admin'),(event,'customer');
 return true;
end $$;
revoke all on function public.prepare_survey_brevo_deliveries(uuid) from public,anon,authenticated;
grant execute on function public.prepare_survey_brevo_deliveries(uuid) to service_role;
-- Each provider attempt is recorded independently. On ambiguous delivery,
-- retain uncertain; never auto-requeue. Parent accepted only if both accepted.
create or replace function public.finish_survey_brevo_delivery(event uuid, kind text, accepted boolean)
returns jsonb language plpgsql security definer set search_path='' as $$
declare new_state text; completed integer; accepted_count integer; uncertain_count integer;
begin
 if kind not in ('admin','customer') or accepted is null then
  raise exception 'Invalid survey delivery completion' using errcode='22023';
 end if;
 perform 1 from public.survey_notification_events where id=event for update;
 if not found then raise exception 'Unknown survey notification event' using errcode='22023'; end if;
 update public.survey_notification_deliveries
 set state=case when accepted then 'accepted' else 'uncertain' end,
     finished_at=clock_timestamp()
 where event_id=event and recipient_kind=kind and state='sending'
 returning state into new_state;
 if new_state is null then
  raise exception 'Survey delivery already completed or not prepared' using errcode='22023';
 end if;
 select count(*),count(*) filter (where state='accepted'),count(*) filter (where state='uncertain')
 into completed,accepted_count,uncertain_count
 from public.survey_notification_deliveries where event_id=event;
 if completed<>2 then raise exception 'Invalid survey delivery count' using errcode='22023'; end if;
 if accepted_count=2 or uncertain_count>0 then
  update public.survey_notification_events
  set state=case when accepted_count=2 then 'accepted' else 'uncertain' end,
      finished_at=clock_timestamp()
  where id=event and state='sending';
 end if;
 return jsonb_build_object('recipient_kind',kind,'state',new_state,
   'overall_state',case when accepted_count=2 then 'accepted'
                        when uncertain_count>0 then 'uncertain' else 'sending' end);
end $$;
revoke all on function public.finish_survey_brevo_delivery(uuid,text,boolean) from public,anon,authenticated;
grant execute on function public.finish_survey_brevo_delivery(uuid,text,boolean) to service_role;
commit;
