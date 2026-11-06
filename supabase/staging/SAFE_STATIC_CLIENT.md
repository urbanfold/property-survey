# Static-only staging client — Windows instructions and review

Prepared from reviewed development application commit `c773345d436a35c501e9c5cceec08a26b0173434`. Source hashes and exact transformations are recorded in `static-client/MANIFEST.json`. This is a generated test copy, not an exact production artifact or deployment. Original application, payment/credit logic, Edge Functions and database sources are unchanged.

## What to obtain

Use the existing repository checkout on branch `plan/security-remediation-2026-11-03`, containing this commit. If it is only committed locally by the assistant, an approved development-branch push is needed before downloading it from GitHub. Do not retrieve/restore the flagged ZIP or run its launcher. No replacement ZIP is produced. For a computer without Git, each of the eight files can instead be saved through GitHub's **Download raw file** action from the reviewed commit; retain the `vendor` subfolder. Avoid copying rendered web-page text.

Copy ONLY `supabase/staging/static-client` to a dedicated folder, e.g. `%USERPROFILE%\Urbanfold-Staging-Safe`. There must be `index.html`, `app.js`, `configure.js`, `MANIFEST.json`, `SHA256SUMS.txt` and the three `vendor/*.js` files. No launchers or Python scripts belong in this folder. Do not serve the repository root: its application configuration is for production. Do not use the obsolete ZIP or download a whole repository archive as a workaround for its detection.

## Verify before serving

Leave Defender enabled. Obtain an independent Python 3 installation from python.org or the Microsoft Store if Python is not already installed. Respect Windows/organisation restrictions; do not disable them. Open the new static folder in File Explorer, type `powershell` into its address bar and press Enter. No Administrator window is needed. Verify the checksums (this executes PowerShell commands you type, not a downloaded script):

```powershell
Get-Content .\SHA256SUMS.txt | ForEach-Object {
    $expected, $relative = $_ -split '  ', 2
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $relative).Hash.ToLowerInvariant()
    if ($actual -ne $expected) { throw "Checksum mismatch: $relative" }
    Write-Host "OK $relative"
}
```

Git attributes preserve these files byte-for-byte even with Windows automatic line-ending conversion. All seven checksum entries must say OK. The checksum file does not hash itself. It covers MANIFEST.json and the six application files; compare it with the reviewed GitHub commit independently. Checksums establish byte integrity, not antivirus certification. All eight files are static data, but JavaScript executes when opened in the browser.

## Serve this folder only

In that same PowerShell window:

```powershell
py --version
py -m http.server 8794 --bind 127.0.0.1
```

If your independently installed Python has only `python` as its command, use `python --version` and `python -m http.server 8794 --bind 127.0.0.1`. If neither works, install Python through an official source rather than running a downloaded installation script. Leave the server window open. Stop it with Ctrl+C. No CMD/BAT/PS1 launcher, execution-policy override, firewall change, npm install or Administrator rights are required. The standard Python server serves everything in this folder, so keep it free of secrets, links to other folders and unrelated files. It is a local development server, not internet hosting.

Open **http://localhost:8794/** on the same computer. If localhost does not connect but Python reports it is serving, stop before entering credentials and report the error; do not switch browser origins without reviewing recovery redirect settings. If port8794 is busy, identify/close your earlier staging server; do not terminate unfamiliar processes.

## Confirm the staging boundary

The red banner must read **STAGING ONLY — dummy users and fictional surveys**, show project **hexhtduvqzleoazusskh**, **Payments disabled**, and source c773345d436a. Enter only that project's publishable/anon public key in the on-page configuration box. Never use service-role/secret keys. No credentials are packaged. Use a separate browser profile and only dummy staging accounts. New or refreshed tabs require the public key again. SDK Auth sessions may persist in that browser origin; this is not a new offline storage system.

Bootstrap fixes the backend to `https://hexhtduvqzleoazusskh.supabase.co`; legacy anon keys must match that project and role. New publishable keys cannot be decoded to prove project membership, but the endpoint remains fixed. CSP restricts fetch/WebSocket/image traffic to the local origin and staging; remote script sources are blocked. SDK fetch also rejects foreign origins and all Edge Function paths except the existing request-survey-notification path, including encoded/alternative checkout paths. The generated buy function is replaced with a no-network refusal, its button is disabled, and the Stripe checkout redirect code is absent. Existing £6 entitlement reads remain unchanged; the £179 service is not introduced.

Auth/signup/recovery, survey writes, uploads and survey notification actions are still real staging operations if invoked by an operator. This client does not independently prove staging's SMTP/notification/credit configuration. Do not click recovery, signup, Submit or other write actions without their separate approval/configuration checks. This preparation sends nothing.

## Findings and limits

- No .cmd/.bat/.ps1/EXE launchers, server code, package manager or remote installers are included.
- All application scripts load from the same local folder; vendor libraries are byte-identical to reviewed repository copies, with their license notices retained. No runtime CDN dependency is added. Minified vendor code is not a fresh line-by-line third-party supply-chain audit.
- Bootstrap dynamically loads only the local `app.js`. Its `atob` operation decodes a legacy public JWT to check role/project, not an encoded command. Browser tokens are handled by the Supabase SDK, not exported by the launcher (there is none).
- Current F01 temporary recovery, consent controls, F02 gateway path, exports, photos and Leica implementation are retained by source transformation; the only application function replaced is purchase initiation. Generated bootstrap also preserves just type/error/error_code routing flags until app initialization, because the SDK can consume the URL first; no access/refresh token is copied into that bridge. Fresh-tab and refresh recovery are tested locally.
- Local tests intercept all browser HTTP; PostgreSQL regressions use isolated containers. They do not establish live recovery delivery, production security or Windows Defender acceptance. No Windows host/Defender scan was available. Do not override a further security alert.
- Old ZIP/launchers remain in historical repository paths for evidence. They are NOT inputs to the new static client, and remain unsuitable for use. No old ZIP was executed or repackaged.

## Reproducibility / rollback

`python scripts/build_safe_staging_client.py --check` verifies the committed output against recorded source and current source files without serving, fetching, or rewriting. Generation uses `python scripts/build_safe_staging_client.py` on an approved source commit; it writes only the static folder and never a ZIP. `python tests/test_safe_staging_client.py` exercises mocked startup/isolation/payment/CSP/recovery. No script should be run on the user's Windows computer except the independently installed Python HTTP server command above.

Rollback: stop Python with Ctrl+C and close the staging browser profile. Do not restore the flagged ZIP. No deployed code/database/credentials were changed by this preparation, so no database rollback is needed. Existing staging evidence is untouched. Clearing the browser profile would remove local sessions/drafts and needs a separate considered decision.
