# F01 staging acceptance — prepared, not deployed

This is a **staging-only** build of the focused F01 privacy/session work. It is derived from draft PR #9, including PR #8's logout changes. This branch MUST NOT be merged into `main`, and its staging Supabase connection MUST NOT replace production configuration.

## Configuration and scope
- Supabase endpoint: `https://hexhtduvqzleoazusskh.supabase.co` — Urbanfold-Survey-Staging.
- Uses the project's public, legacy **anon** browser API key (not service_role, not a secret key).
- `index.html` includes the visible “STAGING TEST ONLY — No live surveys or payments” banner and a staging asset version.
- `python scripts/check_staging_acceptance_bundle.py` refuses live Supabase references, non-anon browser keys, missing bundled JavaScript or a missing staging banner.
- GitHub Actions **verifies** this branch on push. **Publishing stays restricted to `main`**; staging verification does not host a site or modify either Supabase project.
- Draft PR #9 should continue using the original live target in its code for eventual production integration, subject to separate approval. This isolated branch is exclusively for staging acceptance.

## Before manual browser acceptance
1. Review the GitHub verification run and fix any failing tests.
2. Establish an isolated staging-only hosting address and ensure the staging Auth Site URL/redirect allowlist and `APP_URL` are appropriate. **Do not deploy without explicit authorization.**
3. In browser network tools, confirm Auth, REST, Storage and Edge Functions calls go to the staging project. Stop if any call targets `arnzqizcycesukplmvuc`.
4. Use only test accounts and test property data. Check owner A vs owner B isolation, unexpected expiry + same-user recovery, different account rejection, deliberate logout, two-tab logout, private signed photos and exports.
5. Keep Stripe test/sandbox isolated and staging notification capture-only; do not send real customer emails or take payments. Validate settings before triggering either workflow.
6. Record observed result, timestamp and any defect against GitHub issue #7. Approval for production must be obtained separately.

## Status
Prepared staging branch and local fail-closed configuration check only. **Not deployed, not staging-tested with real accounts, not approved for production.**
