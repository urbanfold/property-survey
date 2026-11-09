# Production Auth email configuration — owner report, 4 November 2026

The owner reports that the production Urbanfold Supabase Auth email setup is now working:

- Email confirmation is enabled.
- Custom SMTP is configured through Brevo using the authenticated `urbanfold.uk` domain.
- Email verification was successfully tested by the owner.
- Password-recovery email and recovery flow were successfully tested by the owner.

**Evidence classification:** owner-reported successful production tests; not independently inspected or exercised by this assistant. SMTP host/port/TLS details, sender identity, SMTP credentials, DNS records, rate limits, Auth redirect allowlist, token/session lifetimes, enumeration protections and MFA configuration were not supplied or verified. No credentials or customer email contents are recorded here. Domain authentication is recorded as reported, not an independent assertion of particular SPF/DKIM/DMARC records.

This updates the original audit's unavailable/untested Auth email-delivery status. It does not verify production RLS/Storage isolation, session expiry behaviour, F01 deployment, F02 delivery or the exact live `get_survey_allowance()` warning. Production SMTP must not be copied to staging or used to send staging dummy notifications. Any new staging email-delivery test needs its own approved test-only inbox/sender configuration; administratively confirmed dummy users can test ownership without production SMTP.

No production setting, SQL, Stripe configuration, customer record or application deployment was changed by the assistant for this documentation update. No credentials were requested, read or copied.

## Development and staging status reconciliation

- The approved F01 commit `2ea131a` was previously pushed to `plan/security-remediation-2026-11-03`; remote PR #1 head was checked at that commit. The user had confirmed it was a draft. Later API inspection remained Forbidden, so newer remote check results are not independently known. Nothing was merged or marked ready by the assistant.
- The fresh staging package was committed locally as `ce0ff8f` and was not pushed by the assistant.
- The owner supplied staging project reference `hexhtduvqzleoazusskh`, and screenshots showed the setup completion marker in `Urbanfold-Survey-Staging` followed by all 12 metadata verification rows returning true. These are user-provided staging execution/configuration evidence, not direct assistant database access.
- Staging is therefore **already initialised on the available evidence**. Do not rerun the fresh-project baseline/setup bundle or reset it. No dummy-user UUIDs, real bearer-token ownership tests, Storage API upload tests, staging client origin or deployed staging notification function have yet been confirmed to the assistant.

Next staging activity is review/inspection of the existing schema inventory and target project, followed by authorised dummy-user/API tests. Production remains separate. See `supabase/staging/CURRENT_STATUS.md` for the reviewed first step and outstanding requirements.
