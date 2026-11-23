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
    finally:
        subprocess.run(['docker','rm','-f',name],capture_output=True)

if __name__ == '__main__':
    main()
