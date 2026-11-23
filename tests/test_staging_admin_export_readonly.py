"""Offline RLS test for the proposed STAGING-ONLY admin export SELECT policies.

Runs against disposable network-isolated PostgreSQL Docker, never Supabase.
"""
from pathlib import Path
import json
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'postgres:17-alpine@sha256:eee6c6e1b0894fa4fe0075eb054af9fd1cf39a35321c2d4110626cfe506411fb'
ADMIN = 'b83f87d8-abf2-4800-beab-8279917804c7'

def main():
    name = 'urbanfold-staging-export-' + uuid.uuid4().hex[:10]
    def sql(statement, expected_error=None):
        result = subprocess.run(
            ['docker','exec','-i',name,'psql','-X','-q','-t','-A','-v','ON_ERROR_STOP=1','-U','postgres'],
            input=statement, text=True, capture_output=True)
        if expected_error:
            assert result.returncode != 0 and expected_error in result.stderr, (statement, result.stderr)
        else:
            assert result.returncode == 0, (statement, result.stderr)
        return result.stdout.strip()
    def as_user(identity, body, email='customer@example.test', role='authenticated'):
        claims=json.dumps({'sub':identity,'role':role,'email':email})
        return f"set role {role}; set request.jwt.claims = '{claims}'; {body}"
    try:
        subprocess.run(['docker','run','--rm','-d','--name',name,'--network','none',
                        '-e','POSTGRES_HOST_AUTH_METHOD=trust',IMAGE],check=True,capture_output=True)
        for _ in range(100):
            if subprocess.run(['docker','exec',name,'pg_isready','-h','127.0.0.1','-U','postgres'],capture_output=True).returncode == 0:
                break
            time.sleep(.1)
        else: raise AssertionError('test PostgreSQL did not start')
        sql((ROOT/'tests/database_fixture.sql').read_text())
        sql((ROOT/'supabase/001_secure_access.sql').read_text())
        owner_a, owner_b = str(uuid.uuid4()), str(uuid.uuid4())
        prop_a, prop_b, room_a = (str(uuid.uuid4()) for _ in range(3))
        sql(f"insert into auth.users values ('{ADMIN}'),('{owner_a}'),('{owner_b}');"
            f"insert into properties(id,user_id,address,postcode) values ('{prop_a}','{owner_a}','DUMMY A','A'),('{prop_b}','{owner_b}','DUMMY B','B');"
            f"insert into rooms(id,property_id,room_name) values('{room_a}','{prop_a}','Dummy room');"
            f"insert into room_photos(room_id,photo_url) values('{room_a}','storage://room-photos/{prop_a}/photo.jpg');"
            f"insert into storage.objects(bucket_id,name) values('room-photos','{prop_a}/photo.jpg');")
        # Before the proposed policy, new staging admin can only see their own rows.
        assert sql(as_user(ADMIN,'select count(*) from properties;',email='urbanfolduk+staging-reg-01@gmail.com')) == '0'
        assert sql(as_user(owner_a,'select count(*) from properties;')) == '1'
        assert sql(as_user(owner_b,'select count(*) from room_photos;')) == '0'
        assert sql(as_user(owner_b,'select count(*) from storage.objects;')) == '0'
        sql((ROOT/'tests/staging_admin_export_readonly_proposal.sql').read_text())

        # New staging admin can READ both customers' survey data and the private photo.
        assert sql(as_user(ADMIN,'select count(*) from properties;',email='urbanfolduk+staging-reg-01@gmail.com')) == '2'
        assert sql(as_user(ADMIN,'select count(*) from rooms;',email='urbanfolduk+staging-reg-01@gmail.com')) == '1'
        assert sql(as_user(ADMIN,'select count(*) from room_photos;',email='urbanfolduk+staging-reg-01@gmail.com')) == '1'
        assert sql(as_user(ADMIN,'select count(*) from storage.objects;',email='urbanfolduk+staging-reg-01@gmail.com')) == '1'
        # Ordinary A and B have strictly separate SELECT, and anon sees nothing.
        assert sql(as_user(owner_a,'select count(*) from properties;')) == '1'
        assert sql(as_user(owner_b,'select count(*) from properties;')) == '1'
        assert sql(as_user(owner_b,'select count(*) from room_photos;')) == '0'
        assert sql(as_user(owner_b,'select count(*) from storage.objects;')) == '0'
        assert sql('set role anon; select count(*) from properties;') == '0'
        assert sql('set role anon; select count(*) from storage.objects;') == '0'
        print('PASS read-only staging admin sees dummy A/B surveys and photo; B and anon remain blocked')

        # Existing UPDATE policies must NOT allow the new staging admin to modify cross-user data.
        assert sql(as_user(ADMIN,f"with changed as (update properties set address='modified' where id='{prop_a}' returning id) select count(*) from changed;",email='urbanfolduk+staging-reg-01@gmail.com')) == '0'
        assert sql(as_user(ADMIN,f"with changed as (update rooms set room_name='modified' where id='{room_a}' returning id) select count(*) from changed;",email='urbanfolduk+staging-reg-01@gmail.com')) == '0'
        assert sql(as_user(ADMIN,f"with changed as (update storage.objects set name='modified' where bucket_id='room-photos' returning id) select count(*) from changed;",email='urbanfolduk+staging-reg-01@gmail.com')) == '0'
        sql(as_user(ADMIN,f"insert into properties(user_id,address,postcode) values('{owner_a}','Injected','X');",email='urbanfolduk+staging-reg-01@gmail.com'), 'row-level security')
        sql(as_user(ADMIN,f"insert into storage.objects(bucket_id,name) values('room-photos','{prop_a}/injected.jpg');",email='urbanfolduk+staging-reg-01@gmail.com'), 'row-level security')
        assert sql(as_user(owner_a,f"with changed as (update properties set address='owner-edit' where id='{prop_a}' returning id) select count(*) from changed;")) == '1'
        print('PASS staging admin cannot alter others records; owner edits preserved')
    finally:
        subprocess.run(['docker','rm','-f',name],capture_output=True)

if __name__=='__main__':
    main()
