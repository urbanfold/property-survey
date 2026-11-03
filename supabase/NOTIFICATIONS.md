# Proposed F02 survey notification gateway — review before deployment

**Development candidate only. No production migration, function deployment, secret change or webhook rotation has been performed.**

This gateway preserves existing payload fields and the distinction between a saved survey and an accepted notification. It does not alter the £6 credit flow or implement the separate £179 Essential Feasibility service.

## Candidate files

- `003_survey_notifications.sql`: additive event table and service-only claim/completion functions.
- `functions/_shared/notifications.mjs`: authenticated, bounded notification handler.
- `functions/request-survey-notification/index.ts`: Edge Function entry point.
- `dashboard/request-survey-notification.ts`: generated single-file dashboard deployment.
- Client integration: `app.js` invokes the gateway with the property ID only.

## Authorisation and compatibility

The endpoint verifies the bearer session through Supabase Auth, requires a confirmed email, then reads the property using the user's token and existing RLS. The SQL helper independently checks the actor against the actual Auth record and owner/admin relationship. A saved `last_submitted_at` marker is required; the current application does not depend on changing `properties.status` to mark submission.

A professional's client contact can differ from the professional's login email. The saved `client_email` remains the intended recipient field; it is not used to grant data access. Browser-provided recipient, address, actor or revision overrides are rejected. **This preserves owner-authorised client notifications, not independent proof of the client's consent/control of that address.** Confirm this recipient policy before releasing; a verified-contact workflow is a separate enhancement.

Payload fields remain `client_email`, `address`, `surveyor_name`, `property_id`, and a server-generated 64-character `submission_id`. Current Zapier actions/templates must be checked in staging; their configuration was not available to this audit. No webhook or service-role key is embedded in client JavaScript.

## Deduplication and proposed limits

The event identity is property ID plus a server-computed saved-content fingerprint. The submitted timestamp is also checked; repeated submissions of unchanged content reuse the prior event. Claims are serialised, a unique constraint prevents concurrent duplicates and an accepted event is not re-sent. The proposed rolling 24-hour caps are **20 events per requesting account** and **5 per property**; review these for independent professionals' actual usage before approving them. Failures/uncertain attempts count toward caps.

Only the distance-survey notification event is recorded; no survey-credit purchase or £179 entitlement is created. The new table has RLS enabled and no anonymous/authenticated direct access. Helper EXECUTE grants are service-role-only and search paths are fixed.

If delivery times out or finishing the receipt fails, the result remains uncertain/sending and is not automatically re-sent. This avoids blind duplicates but can require reconciliation. The recipient automation may not honour the outbound idempotency header; **exactly-once email delivery is not guaranteed**. No public retry/override endpoint exists. Operator reconciliation must be designed/approved before relying on automatic recovery.

## Approval and rollout gates

1. Approve the recipient policy, proposed caps, event retention and the F01 device-draft policy documented in the candidate report.
2. Use an isolated Supabase project with a reviewed baseline schema. Do not run `tests/database_fixture.sql` in production.
3. Apply proposed migration 003 in staging only and deploy the new function there. Set server secret `SURVEY_NOTIFICATION_WEBHOOK_URL` to a dummy/test receiver. Supabase injects its standard URL/anon/service-role secrets; never place the service key in browser code or chat. `APP_URL` must match the approved staging origin.
4. Exercise owner/professional A, B and admin with real staging Auth and Storage. Test payload tampering, same/different client email, duplicate claims, limits and ambiguous delivery.
5. Review the exact code/SQL, test evidence and rollback. Obtain explicit approval for each production action.
6. Deploy backend prerequisites before the client. The live client must not invoke a function that has not been installed.
7. Retire/rotate the exposed old Zapier catch URL with approval and update the server secret. Provider-specific rotation may require a replacement Zap; preserve and test the existing actions. Merely copying the old URL into a secret does not revoke its earlier public exposure.
8. Check residual Netlify/old cached clients. Do not restore a public webhook fallback as a rollback. Prefer the existing “survey saved, notification unconfirmed” state while repairing an authenticated path.

No CLI command in this document has been run against a cloud project. The proposed gateway cannot be called successfully in production until its separately approved migration, deployment and secret configuration are in place.

## Tests

Run locally with existing test prerequisites:

```sh
node --test tests/test_notification_handlers.mjs
python tests/test_survey_notifications.py
python tests/test_session_security.py
python tests/test_browser_integration.py
```

HTTP tests use mocked fetchers/intercepted browser routes. SQL tests use a disposable, network-disabled PostgreSQL container. They do not prove real email delivery or live Supabase configuration. Existing credit/billing suites must also pass without changing 600-pence GBP rules.
