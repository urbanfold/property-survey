"""Extra assertions using only the caller's disposable, network-disabled PostgreSQL."""
import json,uuid
from concurrent.futures import ThreadPoolExecutor

def run(sql):
 # Missing/false/null/string metadata never becomes marketing consent; existing
 # confirmed INSERT semantics are explicit, not evidence of an email-link click.
 for value in ['false','null','"true"']:
  person=str(uuid.uuid4())
  sql(f'''insert into auth.users(id,email,email_confirmed_at,raw_user_meta_data) values('{person}','no-consent@example.invalid',now(),'{{"newsletter_subscribed":{value}}}');''')
  assert sql(f"select opted_in from newsletter_preferences where user_id='{person}';")=='f'
  assert sql(f"select newsletter_signup_choice from registration_notification_events where user_id='{person}';")=='f'
 person=str(uuid.uuid4())
 sql(f"insert into auth.users(id,email,email_confirmed_at) values('{person}','missing@example.invalid',now());")
 assert sql(f"select opted_in from newsletter_preferences where user_id='{person}';")=='f'
 assert sql(f"select count(*) from registration_notification_events where user_id='{person}';")=='1'
 for role in ['anon','authenticated']:
  sql(f'set role {role};select recover_stale_registration_notifications();','permission denied')
  sql(f"set role {role};select finish_registration_notification('{uuid.uuid4()}',true,now());",'permission denied')
 # Separate prior consent-test events from the controlled queue and rate windows.
 sql("update registration_notification_events set state='uncertain',claim_started_at=clock_timestamp()-interval '2 hours',finished_at=clock_timestamp();")
 people=[str(uuid.uuid4()) for _ in range(55)]
 values=','.join(f"('{p}','rate-{i}@example.invalid',now())" for i,p in enumerate(people))
 sql('insert into auth.users(id,email,email_confirmed_at)values'+values+';')
 def claim(_=None):return json.loads(sql('set role service_role;select claim_registration_notification();'))
 with ThreadPoolExecutor(max_workers=8) as pool:attempts=list(pool.map(claim,range(10)))
 claimed=[e for e in attempts if 'id' in e];blocked=[e for e in attempts if e.get('status')=='rate_limited']
 assert len(claimed)==5 and len(blocked)==5,(len(claimed),len(blocked))
 assert len({e['id'] for e in claimed})==5
 assert all(1<=e['retry_after_seconds']<=60 for e in blocked)
 assert sql("select count(*) from registration_notification_events where state='pending';")=='50'
 # Advance claim timestamps only in this isolated test DB, not a real project.
 sql("update registration_notification_events set claim_started_at=clock_timestamp()-interval '2 minutes' where state='sending';")
 for batch in range(9):
  events=[json.loads(s) for s in sql('set role service_role;select claim_registration_notification() from generate_series(1,5);').splitlines()]
  assert len(events)==5 and all('id' in e for e in events),(batch,events)
  sql("update registration_notification_events set claim_started_at=clock_timestamp()-interval '2 minutes' where state='sending';")
 assert sql("select count(*) from registration_notification_events where claim_started_at>clock_timestamp()-interval '1 hour';")=='50'
 blocked=claim();assert blocked['status']=='rate_limited' and 3000<=blocked['retry_after_seconds']<=3600
 assert sql("select count(*) from registration_notification_events where state='pending';")=='5'
 # A slot that has aged past the hour permits exactly one further claim.
 sql("update registration_notification_events set claim_started_at=clock_timestamp()-interval '1 hour 1 second' where id=(select id from registration_notification_events where state='sending' order by id limit 1);")
 active=claim();assert 'id' in active
 # Completion must acknowledge persisted state and match this exact claim.
 result=json.loads(sql(f"set role service_role;select finish_registration_notification('{active['id']}',true,'2000-01-01');"))
 assert result['state']=='sending'
 result=json.loads(sql(f"set role service_role;select finish_registration_notification('{active['id']}',true,'{active['claim_started_at']}');"))
 assert result['state']=='accepted'
 assert claim()['status']=='rate_limited'
 assert sql("select count(*) from registration_notification_events where state='pending';")=='4'
 # Crash after claim: never reset to pending and never overwrite uncertainty
 # if an obsolete worker later tries to mark a recovered claim accepted.
 stale=sql("select id from registration_notification_events where state='sending' order by id limit 1;")
 sql(f"update registration_notification_events set claim_started_at=clock_timestamp()-interval '6 minutes' where id='{stale}';")
 pending=sql("select count(*) from registration_notification_events where state='pending';")
 assert sql('set role service_role;select recover_stale_registration_notifications();')=='1'
 assert sql(f"select state||':'||completion_reason from registration_notification_events where id='{stale}';")=='uncertain:worker_interrupted'
 sql(f"set role service_role;select finish_registration_notification('{stale}',true);")
 assert sql(f"select state from registration_notification_events where id='{stale}';")=='uncertain'
 result=json.loads(sql(f"set role service_role;select finish_registration_notification('{stale}',true,now());"))
 assert result['state']=='uncertain'
 assert sql("select count(*) from registration_notification_events where state='pending';")==pending
 assert sql('set role service_role;select recover_stale_registration_notifications();')=='0'
 # Claim path also recovers stale attempts even when the delivery cap blocks it.
 stale=sql("select id from registration_notification_events where state='sending' order by id limit 1;")
 sql(f"update registration_notification_events set claim_started_at=clock_timestamp()-interval '6 minutes' where id='{stale}';")
 assert claim()['status']=='rate_limited'
 assert sql(f"select state from registration_notification_events where id='{stale}';")=='uncertain'
 # Reapplying migration must conservatively account for old-version attempts.
 from pathlib import Path
 migration=(Path(__file__).resolve().parents[1]/'supabase/004_verified_registration_notifications.sql').read_text()
 sql(f"update registration_notification_events set claim_started_at=null where id='{stale}';")
 sql(migration)
 assert sql(f"select claim_started_at>clock_timestamp()-interval '1 minute' from registration_notification_events where id='{stale}';")=='t'
 print('PASS atomic concurrent 5/minute and 50/hour dispatch limits, rolling expiry, deferred pending queue, stale sending recovery without requeue/late overwrite, restricted recovery RPC and strict non-consent defaults')
