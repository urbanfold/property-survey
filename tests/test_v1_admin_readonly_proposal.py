"""Isolated V1 administrator read-only RLS proposal test. Never connects to Supabase."""
from pathlib import Path
import json
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'postgres:17-alpine@sha256:eee6c6e1b0894fa4fe0075eb054af9fd1cf39a35321c2d4110626cfe506411fb'

def main():
    name = 'urbanfold-v1-rls-' + uuid.uuid4().hex[:10]
    def sql(command, denied=False):
        p = subprocess.run(['docker','exec','-i',name,'psql','-X','-q','-t','-A',
                            '-v','ON_ERROR_STOP=1','-U','postgres'],
                           input=command,text=True,capture_output=True)
        if denied:
            assert p.returncode != 0 and 'row-level security' in p.stderr, p.stderr
        else:
            assert p.returncode == 0, p.stderr
        return p.stdout.strip()
    def user(identity, query, email='customer@example.invalid'):
        jwt = json.dumps({'sub':identity, 'role':'authenticated', 'email':email})
        return "SET ROLE authenticated; SET request.jwt.claims = '" + jwt + "'; " + query
    try:
        subprocess.run(['docker','run','--rm','-d','--name',name,'--network','none',
                        '-e','POSTGRES_HOST_AUTH_METHOD=trust',IMAGE],
                       check=True,capture_output=True)
        for _ in range(100):
            if subprocess.run(['docker','exec',name,'pg_isready','-h','127.0.0.1',
                               '-U','postgres'],capture_output=True).returncode == 0: break
            time.sleep(.1)
        else: raise AssertionError('Postgres did not start')
        sql((ROOT/'tests/database_fixture.sql').read_text())
        sql((ROOT/'supabase/001_secure_access.sql').read_text())
        # Capture the exact policy definitions before the proposed change.
        policy_query = """SELECT coalesce(json_agg(row_to_json(t) ORDER BY t.schemaname,t.tablename,t.policyname),'[]'::json)
            FROM (SELECT schemaname,tablename,policyname,cmd,permissive,roles,qual,with_check
              FROM pg_policies WHERE (schemaname='public' AND tablename IN
              ('properties','extensions','rooms','exterior_photos','extension_photos',
               'sketch_photos','room_photos'))
              OR (schemaname='storage' AND tablename='objects')) t;"""
        original_policies = json.loads(sql(policy_query))
        a,b,admin = [str(uuid.uuid4()) for _ in range(3)]
        pa,pb,room = [str(uuid.uuid4()) for _ in range(3)]
        sql(f"INSERT INTO auth.users VALUES('{a}'),('{b}'),('{admin}');"
            f"INSERT INTO properties(id,user_id,address,postcode) VALUES"
            f"('{pa}','{a}','House A','A'),('{pb}','{b}','House B','B');"
            f"INSERT INTO rooms(id,property_id,room_name) VALUES('{room}','{pa}','Kitchen');"
            f"INSERT INTO storage.objects(bucket_id,name) VALUES('exterior-photos','{pa}/photo.jpg');")
        sql((ROOT/'docs/V1_LIVE_ADMIN_READONLY_RLS_REVIEW.sql').read_text())
        adm = lambda statement: user(admin,statement,'urbanfolduk@gmail.com')
        assert sql(adm('SELECT count(*) FROM properties;')) == '2'
        assert sql(adm('SELECT count(*) FROM rooms;')) == '1'
        assert sql(adm('SELECT count(*) FROM storage.objects;')) == '1'
        assert sql(user(b,'SELECT count(*) FROM rooms;')) == '0'
        assert sql(user(b,'SELECT count(*) FROM storage.objects;')) == '0'
        assert sql('SET ROLE anon; SELECT count(*) FROM properties;') == '0'
        assert sql('SET ROLE anon; SELECT count(*) FROM storage.objects;') == '0'
        # Own writes still function, and creating survey data for others is rejected.
        sql(user(a,f"UPDATE properties SET notes='owner edit' WHERE id='{pa}';"))
        sql(user(a,f"INSERT INTO rooms(property_id,room_name) VALUES('{pa}','Office');"))
        sql(user(a,f"INSERT INTO storage.objects(bucket_id,name) VALUES('exterior-photos','{pa}/owner.jpg');"))
        sql(user(b,f"INSERT INTO rooms(property_id,room_name) VALUES('{pa}','Intrusion');"),denied=True)
        sql(user(b,f"INSERT INTO storage.objects(bucket_id,name) VALUES('exterior-photos','{pa}/intrusion.jpg');"),denied=True)
        # Admin can read but cannot change or insert somebody else's records.
        sql(adm(f"INSERT INTO rooms(property_id,room_name) VALUES('{pa}','Intrusion');"),denied=True)
        sql(adm(f"INSERT INTO properties(user_id,address,postcode) VALUES('{a}','Intrusion','X');"),denied=True)
        sql(adm(f"INSERT INTO storage.objects(bucket_id,name) VALUES('exterior-photos','{pa}/intrusion.jpg');"),denied=True)
        assert sql(adm(f"WITH changed AS (UPDATE properties SET notes='bad' WHERE id='{pa}' RETURNING id) SELECT count(*) FROM changed;")) == '0'
        assert sql(adm(f"WITH changed AS (UPDATE rooms SET room_name='bad' WHERE id='{room}' RETURNING id) SELECT count(*) FROM changed;")) == '0'
        assert sql(adm(f"WITH changed AS (DELETE FROM rooms WHERE id='{room}' RETURNING id) SELECT count(*) FROM changed;")) == '0'
        assert sql(user(a,f"SELECT notes FROM properties WHERE id='{pa}';")) == 'owner edit'
        print('PASS: owners read/write, admin read only, other customers and anonymous denied, private photo storage')
        # Reconstruct a rollback from the actual pre-migration policies, not from
        # assumptions about their expressions. Exercise rollback only in this
        # isolated Docker database. Live rollout needs a fresh policy snapshot.
        originals = {(p['schemaname'],p['tablename'],p['policyname']):p for p in original_policies}
        current = json.loads(sql(policy_query))
        new_policies = [p for p in current if (p['schemaname'],p['tablename'],p['policyname']) not in originals]
        assert len(new_policies) == 6 and all(p['policyname']=='urbanfold_v1_admin_select' for p in new_policies)
        rollback = ['BEGIN;']
        for p in new_policies:
            assert p['schemaname']=='public' and p['tablename'] in (
                'extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos')
            rollback.append(f"DROP POLICY {p['policyname']} ON {p['schemaname']}.{p['tablename']};")
        for p in original_policies:
            assert p['schemaname'] in ('public','storage')
            assert p['policyname'] in ('urbanfold_manage','urbanfold_storage_insert',
                'urbanfold_storage_select','urbanfold_properties_select',
                'urbanfold_properties_insert','urbanfold_properties_update')
            command = f"ALTER POLICY {p['policyname']} ON {p['schemaname']}.{p['tablename']} TO authenticated"
            if p['qual'] is not None:
                command += f" USING ({p['qual']})"
            if p['with_check'] is not None:
                command += f" WITH CHECK ({p['with_check']})"
            rollback.append(command + ';')
        rollback.append('COMMIT;')
        sql('\n'.join(rollback))
        restored = json.loads(sql(policy_query))
        assert restored == original_policies, 'Rollback did not restore exact initial pg_policies snapshot'
        # Original admin write behaviour must be restored by the simulated rollback.
        result = sql(adm(f"BEGIN; UPDATE properties SET notes='rollback-test' "
                         f"WHERE id='{pa}' RETURNING id; ROLLBACK;"))
        assert pa in result, 'Rollback failed to restore original admin policy'
        assert sql(user(a,f"SELECT notes FROM properties WHERE id='{pa}';")) == 'owner edit'
        print('PASS: isolated rollback restores all original policies and admin access without changing survey records')
        # Reapply the migration, then execute the *actual saved live-snapshot
        # rollback script* rather than only a dynamically generated substitute.
        # Its SQL expressions were captured read-only from live, but are run
        # solely against this disposable PostgreSQL fixture.
        sql((ROOT/'docs/V1_LIVE_ADMIN_READONLY_RLS_REVIEW.sql').read_text())
        assert sql(adm('SELECT count(*) FROM properties;')) == '2'
        assert sql(adm(f"WITH changed AS (UPDATE properties SET notes='bad' WHERE id='{pa}' RETURNING id) SELECT count(*) FROM changed;")) == '0'
        sql((ROOT/'docs/V1_ADMIN_RLS_ROLLBACK_SNAPSHOT_2026-11-23.sql').read_text())
        exact_restored = json.loads(sql(policy_query))
        assert exact_restored == original_policies, (
            'Saved live-snapshot rollback differs from isolated fixture baseline: '
            + json.dumps([{'old':a,'new':b} for a,b in zip(original_policies,exact_restored)
                          if a!=b],indent=2))
        assert pa in sql(adm(f"BEGIN; UPDATE properties SET notes='undo' "
                             f"WHERE id='{pa}' RETURNING id; ROLLBACK;"))
        assert sql(user(a,f"SELECT notes FROM properties WHERE id='{pa}';")) == 'owner edit'
        print('PASS: exact saved live-snapshot rollback restores baseline on isolated PostgreSQL')

    finally:
        subprocess.run(['docker','rm','-f',name],capture_output=True)

if __name__ == '__main__':
    main()
