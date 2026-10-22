-- Read-only metadata. No survey rows, passwords, tokens, or secret values.
select jsonb_pretty(jsonb_build_object(
  'columns', (select jsonb_agg(jsonb_build_object(
    'table', table_name, 'column', column_name, 'type', data_type,
    'nullable', is_nullable, 'default', column_default))
    from information_schema.columns
    where table_schema = 'public' and table_name in (
      'properties','extensions','rooms','exterior_photos',
      'extension_photos','sketch_photos','room_photos')),
  'row_security', (select jsonb_agg(jsonb_build_object(
    'table', c.relname, 'enabled', c.relrowsecurity))
    from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public' and c.relkind = 'r'
      and c.relname in ('properties','extensions','rooms','exterior_photos',
        'extension_photos','sketch_photos','room_photos')),
  'policies', (select jsonb_agg(to_jsonb(p)) from pg_policies p
    where schemaname in ('public','storage')),
  'buckets', (select jsonb_agg(jsonb_build_object(
    'id', id, 'public', public, 'file_size_limit', file_size_limit,
    'allowed_mime_types', allowed_mime_types)) from storage.buckets
    where id in ('exterior-photos','sketch-photos','room-photos'))
)) as survey_database_diagnostics;
