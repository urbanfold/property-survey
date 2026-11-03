"""Static staging-package checks only. No SQL execution, DB, Docker or network."""
from pathlib import Path
import hashlib
import importlib.util
import re

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / 'supabase/staging'


def main():
    spec = importlib.util.spec_from_file_location('staging_builder', ROOT / 'scripts/build_staging_setup.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    generated = (STAGING / 'setup.sql').read_text()
    assert generated == builder.build(), 'Generated bundle drift'
    positions = []
    for name in builder.PARTS:
        source = (ROOT / name).read_text()
        marker = f'-- BEGIN SOURCE {name}\n-- SHA256 {hashlib.sha256(source.encode()).hexdigest()}\n'
        positions.append(generated.index(marker))
        assert marker + source + f'\n-- END SOURCE {name}' in generated
    assert positions == sorted(positions)

    baseline = (STAGING / '000_fresh_baseline.sql').read_text()
    fixture = (ROOT / 'tests/database_fixture.sql').read_text()
    expected = fixture[fixture.index('create table public.properties'):fixture.index('create table storage.buckets')]
    expected = expected.replace('references properties(id)', 'references public.properties(id)').replace('references rooms(id)', 'references public.rooms(id)')
    assert expected in baseline, 'Original table reconstruction drifted from reviewed fixture'
    names = set(re.findall(r'create table(?: if not exists)? public\.(\w+)', generated, re.I))
    assert names == {'properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos',
                     'survey_free_allocations','survey_credit_purchases','survey_credit_revocations','survey_notification_events'}
    assert len(re.findall(r'create index urbanfold_', baseline, re.I)) == 7
    for table in names - {'survey_free_allocations','survey_credit_purchases','survey_credit_revocations','survey_notification_events'}:
        assert f'alter table public.{table} enable row level security;' in baseline
    assert baseline.index("raise exception 'Existing Urbanfold objects found") < baseline.index('create table public.properties')
    for forbidden in (r'create\s+role', r'create\s+(?:or\s+replace\s+)?function\s+auth\.', r'create\s+table\s+(?:auth|storage)\.', r'insert\s+into\s+(?:auth\.users|storage\.objects)', r'\bdrop\s+(?:table|schema)'):
        assert not re.search(forbidden,baseline,re.I),forbidden
    for bucket in ['exterior-photos','sketch-photos','room-photos']:
        assert f"('{bucket}','{bucket}',false,null,null)" in baseline
    assert 'from public,anon,authenticated;' in baseline
    assert 'grant select,insert,update on public.properties to authenticated;' in baseline
    assert 'grant select,insert,update,delete on public.extensions' in baseline

    billing = (ROOT / 'supabase/002_survey_purchases.sql').read_text()
    assert 'check (amount_total = 600)' in billing and "check (currency = 'gbp')" in billing
    assert 'p.live_mode and p.redeemed_property_id is null' in billing
    assert 'seed_dummy_credit' not in generated and 'f0000000-0000' not in generated
    for seed in ['seed_dummy_surveys.sql','seed_dummy_credit.sql']:
        source = (STAGING / seed).read_text()
        assert 'obj_description' in source and '@example.invalid' in source and 'urbanfold.staging_setup' in source
        assert not re.search(r'insert\s+into\s+(?:auth\.users|storage\.objects)',source,re.I)
    assert '["Single"]' in (STAGING / 'seed_dummy_surveys.sql').read_text()
    for file in ['metadata_readonly.sql','verify_readonly.sql']:
        source = (STAGING / file).read_text()
        executable = re.sub(r'--[^\n]*','',source)
        executable = re.sub(r"'(?:''|[^'])*'", "''", executable)
        assert not re.search(r'\b(insert|update|delete|drop|alter|create|grant|revoke)\b',executable,re.I),file
    sql_files = list(STAGING.glob('*.sql'))
    for file in sql_files:
        source = file.read_text()
        assert 'arnzqizcycesukplmvuc' not in source
        assert not re.search(r'\b(?:sk_(?:live|test)_[A-Za-z0-9]{8,}|whsec_[A-Za-z0-9]{8,})',source)
    print('PASS static bundle/source-hash parity, 11-table reconstruction, fresh guards, grants/RLS declarations, private bucket declarations, unchanged 600-pence contract, separate dummy seeds and read-only query boundaries')
    print('NO SQL EXECUTED. These checks do not establish PostgreSQL/Supabase semantic validity or live security.')

if __name__ == '__main__':
    main()
