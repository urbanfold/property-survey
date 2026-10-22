"""Run access-policy tests in an isolated PostgreSQL Docker container, never production."""
from pathlib import Path
import json
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'postgres:17-alpine@sha256:eee6c6e1b0894fa4fe0075eb054af9fd1cf39a35321c2d4110626cfe506411fb'

def main():
    name = 'urbanfold-policy-test-' + uuid.uuid4().hex[:10]
    def sql(statement, succeeds=True):
        result = subprocess.run(['docker','exec','-i',name,'psql','-X','-q','-t','-A','-v','ON_ERROR_STOP=1','-U','postgres'],
                                input=statement, text=True, capture_output=True)
        if succeeds and result.returncode:
            raise AssertionError(result.stderr)
        if not succeeds:
            assert result.returncode, 'Expected policy denial but SQL succeeded'
            assert 'row-level security' in result.stderr, result.stderr
        return result.stdout.strip()
    try:
        subprocess.run(['docker','run','--rm','-d','--name',name,'--network','none',
                        '-e','POSTGRES_HOST_AUTH_METHOD=trust',IMAGE], check=True, capture_output=True)
        for _ in range(100):
            if subprocess.run(['docker','exec',name,'pg_isready','-h','127.0.0.1','-U','postgres'],capture_output=True).returncode == 0:
                break
            time.sleep(0.1)
        else:
            raise AssertionError('Test PostgreSQL did not start')
        sql(ROOT.joinpath('tests/database_fixture.sql').read_text())
        migration = ROOT.joinpath('supabase/001_secure_access.sql').read_text()
        sql(migration)
        sql(migration)  # Repeatable application must not damage data or fail.
        owner, other, admin = [str(uuid.uuid4()) for _ in range(3)]
        p1, p2, room1 = [str(uuid.uuid4()) for _ in range(3)]
        sql(f"insert into auth.users values('{owner}'),('{other}'),('{admin}');"
            f"insert into properties(id,user_id,address,postcode) values('{p1}','{owner}','one','A'),('{p2}','{other}','two','B');"
            f"insert into rooms(id,property_id,room_name) values('{room1}','{p1}','Kitchen');"
            f"insert into room_photos(room_id,photo_url) values('{room1}','storage://room-photos/{p1}/photo.jpg');"
            f"insert into storage.objects(bucket_id,name) values('room-photos','{p1}/photo.jpg');")
        def as_user(identity, body, admin_email=False):
            claims = json.dumps({'sub':identity,'role':'authenticated','email':'urbanfolduk@gmail.com' if admin_email else 'person@example.test'})
            return f"set role authenticated; set request.jwt.claims = '{claims}'; {body}"
        assert sql(as_user(owner,'select count(*) from properties;')) == '1'
        assert sql(as_user(other,'select count(*) from rooms;')) == '0'
        for table in ['extensions','exterior_photos','extension_photos','sketch_photos']:
            extra_columns, extra_values = ('', '') if table == 'extensions' else (',photo_url', ",'storage://exterior-photos/test'")
            if table == 'exterior_photos': extra_columns += ',elevation_type'; extra_values += ",'front'"
            sql(f"insert into {table}(property_id{extra_columns}) values('{p1}'{extra_values});")
            assert sql(as_user(owner,f'select count(*) from {table};')) == '1'
            assert sql(as_user(other,f'select count(*) from {table};')) == '0'
            assert sql(as_user(admin,f'select count(*) from {table};',True)) == '1'
            sql(as_user(owner,f"update {table} set property_id='{p2}' where property_id='{p1}';"),False)

        assert sql(as_user(owner,'select count(*) from room_photos;')) == '1'
        assert sql(as_user(other,'select count(*) from room_photos;')) == '0'
        assert sql(as_user(admin,'select count(*) from properties;',True)) == '2'
        assert sql(as_user(admin,'select count(*) from room_photos;',True)) == '1'
        assert sql(as_user(other,"select count(*) from storage.objects;")) == '0'
        assert sql(as_user(owner,"select count(*) from storage.objects;")) == '1'
        assert sql(as_user(admin,"select count(*) from storage.objects;",True)) == '1'
        assert sql('set role anon; select count(*) from properties;') == '0'
        assert sql('set role anon; select count(*) from storage.objects;') == '0'
        sql(as_user(owner,f"update rooms set property_id='{p2}' where id='{room1}';"),False)
        sql(as_user(other,f"insert into rooms(property_id,room_name) values('{p1}','Injected');"),False)
        sql(as_user(other,f"insert into properties(user_id,address,postcode) values('{owner}','Injected','X');"),False)
        sql(as_user(owner,f"update properties set user_id='{other}' where id='{p1}';"),False)
        sql(as_user(other,f"insert into storage.objects(bucket_id,name) values('room-photos','{p1}/injected.jpg');"),False)
        assert sql(as_user(other,f"with changed as (update properties set address='Injected' where id='{p1}' returning id) select count(*) from changed;")) == '0'
        print('PASS owner isolation, private storage, admin access, anonymous denial, forged ownership denial')
        sql(migration)
        assert sql('select count(*) from properties;') == '2'
        assert sql('select count(*) from storage.objects;') == '1'
        # Unexpected policies must roll back the whole migration instead of leaving access open.
        sql('create policy unexpected_public_read on properties for select using (true);')
        result = subprocess.run(['docker','exec','-i',name,'psql','-X','-q','-v','ON_ERROR_STOP=1','-U','postgres'],
                                input=migration,text=True,capture_output=True)
        assert result.returncode and 'Additional access policies exist' in result.stderr
        assert sql("select count(*) from pg_policies where policyname='unexpected_public_read';") == '1'
        print('PASS transactional, repeatable migration and fail-closed handling of unknown policies')
    finally:
        subprocess.run(['docker','rm','-f',name],capture_output=True)

if __name__ == '__main__':
    main()
