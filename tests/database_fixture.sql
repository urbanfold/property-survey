-- Isolated test database, modelled on the user's 2026-10-22 diagnostics.
-- Never run this fixture against the live Supabase project.
create role anon nologin;
create role authenticated nologin;
create schema auth;
create schema storage;
create function auth.jwt() returns jsonb language sql stable as $$
 select coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb
$$;
create function auth.uid() returns uuid language sql stable as $$
 select nullif(auth.jwt()->>'sub', '')::uuid
$$;
create function storage.foldername(name text) returns text[] language sql immutable as $$
 select (string_to_array(name, '/'))[1:array_length(string_to_array(name, '/'), 1)-1]
$$;
create table auth.users(id uuid primary key);
create table public.properties(
 id uuid primary key default gen_random_uuid(), user_id uuid references auth.users(id),
 surveyor_name text, address text not null, postcode text not null, property_type text,
 notes text, status text default 'in_progress', created_at timestamptz default now(), client_email text
);
create table public.extensions(id uuid primary key default gen_random_uuid(),
 property_id uuid references properties(id), extension_types jsonb, description text,
 width numeric, length numeric, created_at timestamptz default now());
create table public.rooms(id uuid primary key default gen_random_uuid(),
 property_id uuid references properties(id), room_name text not null, shape text,
 dimensions jsonb, additional_measurements text, created_at timestamptz default now());
create table public.exterior_photos(id uuid primary key default gen_random_uuid(),
 property_id uuid references properties(id), elevation_type text not null, photo_url text not null,
 created_at timestamptz default now());
create table public.extension_photos(id uuid primary key default gen_random_uuid(),
 property_id uuid references properties(id), photo_url text not null, created_at timestamptz default now());
create table public.sketch_photos(id uuid primary key default gen_random_uuid(),
 property_id uuid references properties(id), photo_url text not null, created_at timestamptz default now());
create table public.room_photos(id uuid primary key default gen_random_uuid(),
 room_id uuid references rooms(id), photo_url text not null, created_at timestamptz default now());
create table storage.buckets(id text primary key, public boolean not null default false);
create table storage.objects(id uuid primary key default gen_random_uuid(),
 bucket_id text references storage.buckets(id), name text not null);
alter table storage.objects enable row level security;
insert into storage.buckets values('exterior-photos',false),('sketch-photos',false),('room-photos',false);
grant usage on schema auth, storage, public to anon, authenticated;
grant execute on all functions in schema auth, storage to anon, authenticated;
grant select, insert, update, delete on all tables in schema public, storage to anon, authenticated;

-- Reproduce broad legacy rules from the diagnostic result; migration must remove them.
alter table public.properties enable row level security;
create policy "Allow users to view properties" on public.properties for select to authenticated using (true);
create policy "Allow users to update properties" on public.properties for update to authenticated using (true);
create policy "Allow users to insert properties" on public.properties for insert to authenticated with check (true);
create policy "Allow public access to view photos" on storage.objects for select using (true);
create policy "Public Access for Photos" on storage.objects for select using (true);
create policy "Allow authenticated users to upload photos" on storage.objects for insert to authenticated with check (true);
