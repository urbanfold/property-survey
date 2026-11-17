# Staging payment evidence separation — implementation notes

**Status (17 Nov 2026): schema-only prototype in staging. No financial records moved. Production account deletion disabled.**

## Verified source
Both production and staging have `public.survey_credit_purchases.user_id -> auth.users.id ON DELETE CASCADE`. Deleting the Auth account would delete the purchase rows. Production currently has two sandbox purchases and zero live-mode purchases; staging has no purchase rows.

## Created in staging only
`public.staging_retained_payment_evidence` holds a minimal independent payment record: Stripe checkout-session and payment-intent IDs, amount (minor currency units), currency, sandbox/live flag (staging enforces sandbox only), purchase date, retention reason, optional review date, timestamp and an optional deletion-request audit reference. It has **no user_id or customer email** and therefore no Auth cascade. It supports **multiple purchases per deletion request** with unique Stripe IDs. Row level security is enabled; privileges are granted only to the service role, not browser clients.

No real payment information has been copied, and no synthetic payment evidence has been falsely recorded as a successful transaction.

## Still required before any deletion handler
1. Establish a lawful basis and appropriate retention period for receipts, refund and dispute records, including how a customer can exercise erasure rights and how exceptions are documented.
2. Check payment integrity in Stripe before preserving records and decide what constitutes the accounting record of truth.
3. Implement server-only per-purchase preservation with transactionally verifiable source IDs and idempotency, then verify count, amount, mode and identifier equality. Never delete the source if preservation is incomplete or rejected.
4. Exercise this in staging with **clearly labelled synthetic** sandbox records and test repeated requests, multiple purchases, refunded payments, missing Stripe IDs and failures; ensure no survey credit is accidentally created.
5. Add a controlled deletion state machine with separate customer verification, Storage API cleanup, accounting preservation, administrator protections, independent audit, and idempotent notification dispatch.
6. Explicitly retain/disconnect real records only where legally required; don't misrepresent staging test purchases as statutory records. The `public.users` table in production also has an Auth FK that requires an explicit handling path.
7. A production version needs a separate design/migration and independent security review. **Do not deploy staging SQL or live deletion automatically.**

## Current safety position
Live administrator lookup is read-only, live deletion remains disabled, and `SURVEY_PAYMENTS_MODE` remains test.
