# Urbanfold Property Survey

A static browser application backed by Supabase Auth, Postgres, and private Storage.
GitHub Pages can host the website. Netlify is not required. Changing the host alone
does not change how data is stored or repair database permissions.

## Current stabilisation release

This release is prepared for validation, not certified against a live account.
The original Supabase diagnostics established the table/column structure, private
photo buckets, and broad legacy access policies. Automated tests exercise that
structure and the replacement policies. Live verification still requires applying
the reviewed SQL and testing the deployed website with an authorised account.

- Forward steps and **Save progress** on the final Room Details page persist all sections without sending email.
- A save reads the records back and compares details, extension choices, both room
  shapes, measurements, and photo references before claiming cloud success.
- Private photos use expiring authenticated links. Existing public-URL references
  remain readable through the new signing path; the buckets stay private.
- Newer device edits resume automatically when the cloud snapshot they were based
  on is unchanged. Stale or conflicting drafts cannot silently replace cloud data;
  they remain available through an explicit button. Reopening starts at Details.
- Failed writes, missing photos, denied reads, or mismatching readback retain the
  device draft and prevent submission success and notification.
- The ZIP includes every photo category plus text and JSON data. The PDF contains
  property, extension, and room measurements.
- Browser libraries are pinned and served from `vendor/`, with source URLs and checksums.
- The GitHub workflow tests the app before publishing only its website assets.

## One-time Supabase preparation

1. Back up the project's database through your normal Supabase backup process.
2. Review and run `supabase/001_secure_access.sql` in the project's SQL Editor.
   It is transactional and repeatable. It replaces the exact broad policies from
   the diagnostics, restricts rows and storage paths to the owner or the existing
   admin email, and adds a nullable `last_submitted_at` field. It does not delete
   survey records or photos, make buckets public, or create user accounts.
3. The script rolls back if it finds an unknown policy or missing/public survey
   bucket. Review that condition rather than weakening the guard.
4. Run `supabase/diagnostics.sql` to verify the resulting schema and policies.

The existing admin identity is `urbanfolduk@gmail.com`. Its signed Supabase JWT
email is checked by database policies; the UI email check is only an affordance.
All seven survey tables need row-level security enabled. Storage object names
start with their property UUID, which the storage policies check for ownership.

The browser contains only Supabase's existing public anon key. Never put a
service-role key, database password, or private token into website files or GitHub
Pages variables. GitHub Pages has no private server-side environment.

## Publish from GitHub, without manual uploads

1. Open the repository's **Settings → Pages**:
   <https://github.com/urbanfold/property-survey/settings/pages>.
2. Under **Build and deployment**, set the source to **GitHub Actions**.
   Keep the repository's visibility unchanged. Private-repository Pages eligibility
   depends on the GitHub plan; resolve any plan restriction explicitly rather than
   making the repository public as a workaround.
3. Open **Actions → Verify and publish survey app**. Run the workflow on `main`,
   or push a change. A failed verification job blocks publication.
4. Use the URL reported by the successful deployment. The expected project URL is
   `https://urbanfold.github.io/property-survey/`; this is not proof it is live.
5. In Supabase **Authentication → URL Configuration**, add that full URL to allowed
   redirects and use it as the Site URL when cutting over. Keep the Netlify URL
   allowed during migration. Password login uses the same existing account; email
   confirmation/recovery must have the new redirect configured.
6. Confirm the app version in the footer matches the deployed commit's first
   twelve characters. GitHub Actions substitutes it during packaging.

The source does not rely on a domain root, a build system, or Netlify redirects.
Website requests and asset paths work under `/property-survey/`.

## Cutover and acceptance

Do not delete the Netlify project or Supabase data while verifying the replacement.
Device drafts and login sessions belong to the website origin: a Netlify draft
will not automatically appear on GitHub Pages. Cloud records use the same Supabase
project on both hosts. Do not edit the same survey simultaneously on both sites.

After SQL and Pages setup, verify with one clearly labelled test survey:

1. Log in, create property details, and select a type.
2. Add exterior, extension-location, sketch, and room photos; save after each section.
3. Enter standard and L-shaped room measurements and extension details.
4. Reload and reopen. Then use a second browser/device without the first browser's
   local draft and confirm every section and all four photo categories load.
5. Finish once. Confirm the success screen, `last_submitted_at`, actual stored
   records, and email notification. Reopen after submission.
6. As admin, download PDF and ZIP and check their actual contents.
7. With a separate non-admin test account, verify other users' surveys and private
   photos are not accessible through the API, not merely hidden in the dashboard.

Only call the migration complete after those live checks. The automated fixtures
never contact real accounts, send email, or establish live Supabase readiness.

## Password recovery

The login screen's **Forgot password?** action requests a Supabase recovery email.
It redirects to the same registered website root, opens a new-password form, checks
confirmation, and honours backend password policies. Recovery links must be valid;
expired links offer a fresh email request. Refreshing a valid recovery tab retains
its reset screen. After updating, password fields are cleared and the user returns
to login. Reset emails use Supabase Auth, not the survey Zapier webhook. Actual
email delivery requires the project's existing Supabase email sender configuration.

## Development and checks

Use the existing checkout; cloud tasks are already isolated. Do not create a Git
worktree unless explicitly requested. There is no application package installation
or build step. Start a static server from this repository:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Test prerequisites are Python 3.12, Node for syntax checking, Playwright, Chromium,
and Docker for the PostgreSQL policy tests. Do not run test SQL fixtures in Supabase.

```sh
python3 -m pip install -r requirements-dev.txt
python3 -m playwright install chromium
node --input-type=module --check < app.js
python3 tests/test_survey_flow.py
python3 tests/test_browser_integration.py
python3 tests/test_database_policies.py
```

`CHROMIUM_PATH` may select a local browser. Otherwise the tests use system Chromium
when present or Playwright's installed browser. Policy tests use a digest-pinned
PostgreSQL 17 container with no network or persistent volume, then remove it.

## Remaining operational limits

- Saves span multiple REST requests. Failure can leave partial cloud progress; the
  device draft is retained and retries update existing records. There is no
  transactional version locking across concurrent editors. Use one editor per survey.
- Device storage is a best-effort backup, not guaranteed offline storage. Full or
  unavailable storage is reported. Save progress to the cloud before leaving.
- Photo removal deletes the survey reference after a successful cloud save. Bytes
  remain in private storage for recovery; a separate reviewed retention process
  should clean unreferenced objects. No existing photo bytes are deleted by setup.
- Email still uses the existing browser-to-Zapier integration. The app distinguishes
  survey storage from notification acceptance and avoids repeat requests for an
  identical saved version on the same device. It cannot promise exactly-once email
  across devices or resolve a network timeout after remote acceptance. For durable
  server-side notification delivery, replace it with an authenticated Supabase Edge
  Function and outbox before relying on automated retries. The existing webhook URL
  was already public in the original source; this release does not make it secret.
- Leica measurement transfer was never implemented: selecting a Bluetooth device
  did not read measurements. The UI now says manual entry instead of claiming a
  working laser connection. Hardware integration is a separate feature.
