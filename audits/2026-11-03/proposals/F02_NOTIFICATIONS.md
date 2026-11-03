# F02 — targeted fix specification (candidate implemented locally; not deployed)

**Goal:** prevent unauthenticated/spoofed browser-triggered notification requests, keep the trigger secret server-side and bound notification retries/costs. Preserve successful survey saving, existing £6 credits and legitimate professional/client workflows.

**Source identity confirmed:** the owner’s screenshot matches `urbanfold/property-survey` at `6874d8a`; deployed artifact parity remains to be checked. Function/SQL/client candidates now exist on the local branch; see ../CANDIDATE_CHANGES.md. No function, migration, secret or client change was applied to production.

## Proposed request flow

1. After verified survey submission, the browser invokes an authenticated `request-survey-notification` endpoint with the property ID only. Do not accept a browser-provided recipient, address, sender identity or “trusted” submission hash.
2. The endpoint validates the bearer session through Supabase Auth; derive the actor from that response. Reject absent/invalid sessions. Apply the approved confirmed-email/admin rules.
3. Read the property with the user's token so current RLS still decides owner/admin access. Verify the property is a saved eligible submission. Construct the notification payload from saved records, not untrusted request fields.
4. Claim an idempotent notification event server-side for the property and saved submission revision. The local candidate also fingerprints saved content so unchanged-content resubmissions remain deduplicated after a timestamp change. Use a durable unique key so concurrent requests and different browsers cannot create duplicate sends. Apply server-side rate caps appropriate for professional accounts, not one-survey-only assumptions.
5. Send to the existing automation using a server secret (for example `SURVEY_NOTIFICATION_WEBHOOK_URL`). No catch URL or service-role credential is shipped to the browser. Do not log headers, secret values or full client payloads.
6. Persist accepted/pending/failed-or-uncertain delivery state and return a limited status to the authenticated caller. Keep “survey saved” independent from “notification accepted”.
7. If a timeout occurs after possible remote acceptance, do not blindly resend. Without downstream idempotency, exactly-once email delivery cannot be promised. Provide reconciliation/manual retry controls for uncertain events.

## Persistence proposal

Prepare an additive, separately reviewed migration for a notification-event/outbox table, or an equivalent durable mechanism. Do not edit credit tables or infer notification entitlement from Stripe purchases.

Proposed minimum event fields: event ID, property ID, authorised actor ID, saved submission revision, idempotency key, delivery state and timestamps. Minimise retained personal information; use limited error codes rather than storing secrets/raw request bodies.

Use a unique constraint on the agreed submission-event identity, RLS with no anonymous access, and explicit table/function grants. If a definer helper is needed, fix its search path, qualify references, grant only the necessary server role and test negative caller cases. Concurrent event claims/rate counters must be transactional. Account for both owner and admin requests for the same property.

Do not run any proposed migration in production until definitions, existing-data compatibility and rollback have been reviewed and approved.

## Recipient policy — professional users must be supported

A designer/surveyor's login email may differ from the client's `client_email`. Preserve that legitimate distinction. Do not silently change delivery to account-owner-only or force independent professionals onto an Urbanfold-only address.

Two different controls must not be confused:

- **Sender authorisation:** the authenticated professional/homeowner is allowed to request a notification for this saved property.
- **Recipient verification/consent:** the intended recipient is an approved destination for that relationship.

Server-side record lookup prevents body tampering, but an owner can intentionally edit their own `client_email`; lookup alone does not prove the recipient controls or consents to that address. Confirm the current Zapier recipient/template behaviour and approve the recipient rules before implementation. Options include verified client contacts/relationships, bounded owner-authorised notifications with an explicit recipient confirmation step, or a restricted administrative notification route. Rate limits alone are not recipient verification.

Keep newsletter consent separate from survey-service notifications. No marketing subscriptions are created by this fix.

## Required tests

- Anonymous/expired token: reject without contacting the automation.
- Homeowner/professional A requests B's property: reject; do not expose B's metadata.
- Valid owner/professional and intended admin: permitted according to current RLS and agreed recipient rules.
- Forged body recipient, sender, address or revision: ignored/rejected; derive saved data server-side.
- Unsaved/missing/non-submitted property: no send.
- Client email differs from the professional's email: test the approved rule explicitly.
- Duplicate, concurrent and cross-device requests: one event claim, bounded delivery.
- Rate caps, restart, database failure, remote rejection and ambiguous timeout: no unlimited sends and no false “survey lost” message.
- Verify no webhook/service-role secret remains in the deployed client artifact.
- Existing login/signup, saving, photo uploads, admin access and £6 Stripe suites pass without changing price/metadata/ledger rules.

Use a dummy receiver for tests. Never call the real exposed catch URL just to demonstrate the issue.

## Safe deployment order (requires explicit approval)

1. Confirm the real integration and approve recipient/draft-independent notification semantics.
2. Deploy any additive schema and server function to isolated staging; configure a dummy secret/receiver and exercise authorised test accounts.
3. Review concrete code/SQL and rollback. Approve production backend prerequisites before a client cutover.
4. Deploy the client integration only after the authenticated backend is available and tested.
5. Rotate/retire the exposed old catch URL after verifying the new route. This requires access to the actual automation and explicit approval; deleting the URL from source does not revoke it.
6. Verify current and any residual Netlify clients cannot continue using the old trigger. Do not leave an unauthenticated fallback active as a supposed rollback.

This specification now has a locally tested candidate endpoint/outbox implementation. No endpoint/outbox is claimed to exist in production; no secret rotation or deployment has occurred.
