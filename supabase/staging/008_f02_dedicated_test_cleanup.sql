-- PREPARED ONLY. DO NOT RUN UNTIL TEST EVIDENCE HAS BEEN EXPORTED AND REVIEWED.
-- Urbanfold-Survey-Staging ONLY: verify Dashboard ref hexhtduvqzleoazusskh.
-- Destructive ONLY to the exact six fixtures and their matching survey events/receipts.
-- Never run with ongoing notification tests or requests. Wait for all requests to finish.
-- Review deployed DELETE triggers/FKs using f02_property_trigger_preflight.sql first.
-- No schema, permission, Auth, Storage, credit or production changes.
-- Intentionally stops if unexpected children, identities, receipts or credit links exist.
begin;
do $$
declare
 evidence_reviewed boolean := false; -- Change to true ONLY after evidence is retained.
 ids uuid[] := array[
 'f0200000-0000-4000-8000-000000000001'::uuid,
 'f0200000-0000-4000-8000-000000000002'::uuid,
 'f0200000-0000-4000-8000-000000000003'::uuid,
 'f0200000-0000-4000-8000-000000000004'::uuid,
 'f0200000-0000-4000-8000-000000000005'::uuid,
 'f0200000-0000-4000-8000-000000000006'::uuid];
 allocations_before jsonb; purchases_before jsonb; revocations_before jsonb;
 allocations_after jsonb; purchases_after jsonb; revocations_after jsonb;
 deleted_receipts integer; deleted_events integer; deleted_properties integer;
begin
 if not evidence_reviewed then raise exception 'Export and review evidence before enabling cleanup.'; end if;
 if current_user <> 'postgres' or auth.uid() is not null or auth.jwt()->>'role' is not null then
  raise exception 'Use staging SQL Editor as postgres without simulated JWT claims.';
 end if;
 if obj_description('public.properties'::regclass,'pg_class') is distinct from
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.' then
  raise exception 'Reviewed staging baseline required.';
 end if;
 if not exists(select 1 from auth.users where id='9036b71c-4f09-4d1b-9dce-519533c4001e'
   and email='staging-owner-a@example.invalid' and email_confirmed_at is not null)
 or not exists(select 1 from auth.users where id='d72b4323-d71b-4b87-b78a-09896647fddf'
   and email='staging-owner-b@example.invalid' and email_confirmed_at is not null) then
  raise exception 'Confirmed dummy identities do not match.';
 end if;
 perform 1 from public.properties where id=any(ids) order by id for update;
 if (select count(*) from public.properties where id=any(ids)) <> 6 then
  raise exception 'Expected all six fixtures. Already cleaned, missing, or partially installed: inspect; do not bypass.';
 end if;
 if exists(select 1 from unnest(ids) with ordinality x(id,n)
   join public.properties p on p.id=x.id where
   p.user_id is distinct from (case when x.n<=5 then '9036b71c-4f09-4d1b-9dce-519533c4001e'::uuid
   else 'd72b4323-d71b-4b87-b78a-09896647fddf'::uuid end)
   or p.address is distinct from 'DUMMY F02 FIXTURE '||x.n||' - NOT A REAL ADDRESS'
   or p.postcode is distinct from 'ZZ9 9ZZ'
   or p.surveyor_name is distinct from 'DUMMY F02 TEST SURVEYOR') then
  raise exception 'A fixed ID no longer matches its dedicated fixture identity.';
 end if;
 if exists(select 1 from public.survey_free_allocations where property_id=any(ids))
 or exists(select 1 from public.survey_credit_purchases where redeemed_property_id=any(ids)) then
  raise exception 'Fixture has an entitlement link; stop without altering it.';
 end if;
 -- Notification-only fixtures should have no rooms/photos/extensions. Preserve any surprises.
 if exists(select 1 from public.rooms where property_id=any(ids))
 or exists(select 1 from public.extensions where property_id=any(ids))
 or exists(select 1 from public.exterior_photos where property_id=any(ids))
 or exists(select 1 from public.extension_photos where property_id=any(ids))
 or exists(select 1 from public.sketch_photos where property_id=any(ids)) then
  raise exception 'Unexpected child records: stop and review separately; no photo or room cleanup performed.';
 end if;
 perform 1 from public.survey_notification_events where property_id=any(ids) for update;
 if exists(select 1 from public.survey_notification_events e
   join public.properties p on p.id=e.property_id where e.property_id=any(ids)
   and (e.actor_id is distinct from p.user_id or e.state='sending'
        or e.created_at>clock_timestamp()-interval '1 minute')) then
  raise exception 'Unexpected actor, in-flight, or recent event: finish testing and review first.';
 end if;
 -- A receipt must match BOTH an owned fixture event ID and its property payload.
 if exists(select 1 from public.staging_notification_receipts r
   where r.kind='survey' and (
    r.payload->>'property_id' in(select unnest(ids)::text)
    or r.delivery_id in(select id from public.survey_notification_events where property_id=any(ids)))
   and not exists(select 1 from public.survey_notification_events e
     where e.id=r.delivery_id and e.property_id=any(ids)
     and r.payload->>'property_id'=e.property_id::text)) then
  raise exception 'Unexpected or orphan receipt linkage; preserve for investigation.';
 end if;
 select coalesce(jsonb_agg(to_jsonb(x) order by x.user_id),'[]'::jsonb)
 into allocations_before from public.survey_free_allocations x;
 select coalesce(jsonb_agg(to_jsonb(x) order by x.checkout_session_id),'[]'::jsonb)
 into purchases_before from public.survey_credit_purchases x;
 select coalesce(jsonb_agg(to_jsonb(x) order by x.payment_intent_id),'[]'::jsonb)
 into revocations_before from public.survey_credit_revocations x;
 delete from public.staging_notification_receipts r using public.survey_notification_events e
 where r.kind='survey' and r.delivery_id=e.id and e.property_id=any(ids)
 and r.payload->>'property_id'=e.property_id::text;
 get diagnostics deleted_receipts = row_count;
 delete from public.survey_notification_events where property_id=any(ids);
 get diagnostics deleted_events = row_count;
 delete from public.properties where id=any(ids);
 get diagnostics deleted_properties = row_count;
 if deleted_properties<>6 then raise exception 'Unexpected deleted property count; rolling back.'; end if;
 select coalesce(jsonb_agg(to_jsonb(x) order by x.user_id),'[]'::jsonb)
 into allocations_after from public.survey_free_allocations x;
 select coalesce(jsonb_agg(to_jsonb(x) order by x.checkout_session_id),'[]'::jsonb)
 into purchases_after from public.survey_credit_purchases x;
 select coalesce(jsonb_agg(to_jsonb(x) order by x.payment_intent_id),'[]'::jsonb)
 into revocations_after from public.survey_credit_revocations x;
 if allocations_before is distinct from allocations_after
 or purchases_before is distinct from purchases_after
 or revocations_before is distinct from revocations_after then
  raise exception 'Entitlement records changed unexpectedly; rolling back cleanup.';
 end if;
 raise notice 'Removed % dedicated properties, % events, % receipts. No credit records changed.',
 deleted_properties,deleted_events,deleted_receipts;
end $$;
commit;
