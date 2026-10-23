# Survey purchases: operator setup

This release prepares the payment integration. **A GitHub Pages deployment does
not install SQL or deploy Supabase Edge Functions, and Stripe has not been set up.**
Existing surveys and photos remain available. Do not advertise working payments
until the live checks below are complete.

## Behaviour

- One lifetime free property survey per authenticated client account.
- Each £6 GBP payment buys one additional survey, consumed when its property
  details are first saved. No subscription or automatic recurring charge.
- Price is £6 total at Checkout. Stripe processing fees come out of receipts.
  Automatic tax is not enabled; the business must establish its VAT treatment.
- Existing properties are grandfathered, including accounts with several already.
  Their first property uses their free allocation; editing existing properties is free.
- The existing signed admin email is exempt. Submitted addresses are locked for
  clients; the admin can correct them. Measurements and notes remain editable.
- Credits are retained until used. Deleting a property through privileged
  maintenance does not restore a free allocation or spent credit.
- A signed Stripe webhook, not the return URL, grants credit. Duplicate events
  are idempotent. Refunded/disputed unused credits are revoked. Used credits do
  not cause existing surveys or photos to be deleted; handle those cases manually.
- This is an account allowance, not identity verification. Creating more email
  accounts and copying one's own data cannot be completely prevented by it.

## 1. Create Stripe and install the SQL

Create a business Stripe account at https://dashboard.stripe.com/register and
complete its business/bank verification before accepting live payments. Start
in a Stripe sandbox/test environment. No Stripe products or Payment Links need
to be created manually; the server fixes the single item at 600 pence.

In the existing Supabase SQL Editor, use a **new query** for
[002_survey_purchases.sql](002_survey_purchases.sql), after migration 001. Review
and run the whole file. It is transactional and repeatable, adds payment ledger
and allocation tables/functions/triggers, and preserves survey records/photos.
The exact success result begins `Survey allowance installed`.

This turns on the database limit even if payments are still disabled. Clients
can continue existing surveys and new clients retain their free survey; additional
survey buyers will need to wait for Stripe activation.

## 2. Deploy both Supabase functions

For dashboard-only setup, use **Edge Functions → Deploy a new function → Via
Editor**. Name the first function `create-survey-checkout`, replace the entire
`index.ts` template with [dashboard/create-survey-checkout.ts](dashboard/create-survey-checkout.ts),
and deploy. Repeat for `stripe-survey-webhook` using
[dashboard/stripe-survey-webhook.ts](dashboard/stripe-survey-webhook.ts).
Both files are self-contained and contain no secret keys. In each function's
settings, disable **Verify JWT with legacy secret** (wording may vary) and save.
The application handlers perform their own authentication checks as described
below; Stripe cannot send a Supabase JWT.

The dashboard files are generated copies of the same tested shared handler.
After changing that source, run `python scripts/build_dashboard_functions.py`
and redeploy both functions. CI checks that these copies stay current. GitHub
Pages never publishes these files. Dashboard deployments must be updated manually.

Alternatively, use the Supabase CLI from a checkout of this repository. These commands deploy
server code, including its shared module; they do not publish private keys in
GitHub Pages:

```sh
supabase login
supabase link --project-ref arnzqizcycesukplmvuc
supabase functions deploy create-survey-checkout
supabase functions deploy stripe-survey-webhook
```

`supabase/config.toml` disables the gateway JWT check for these functions.
Checkout explicitly validates the caller's bearer token through Supabase Auth;
the webhook explicitly validates Stripe's signature over the unmodified body.
Do not remove those checks. The Stripe endpoint cannot use a Supabase user JWT.

In Supabase **Edge Functions → Secrets**, store these values securely, never in
chat, browser JavaScript, repository files or screenshots:

| Secret | Initial value |
| --- | --- |
| `SURVEY_PAYMENTS_MODE` | `test` (or `disabled` to stop new checkouts) |
| `STRIPE_SECRET_KEY` | Stripe sandbox secret, starting `sk_test_` |
| `STRIPE_WEBHOOK_SECRET` | Signing secret of the sandbox destination, `whsec_…` |

Supabase injects `SUPABASE_URL`, `SUPABASE_ANON_KEY` and
`SUPABASE_SERVICE_ROLE_KEY` for deployed functions. The service role key stays
on the server. `APP_URL` defaults to `https://urbanfold.github.io/property-survey/`;
change it only for a separate deployment, with HTTPS and a trailing slash.

## 3. Add the Stripe event destination

In Stripe's sandbox, add a webhook/event destination for this URL:

```
https://arnzqizcycesukplmvuc.supabase.co/functions/v1/stripe-survey-webhook
```

Payment methods are managed in Stripe’s Dashboard settings. The Checkout request
does not send the removed `payment_method_types` parameter. Keep cards enabled
in the sandbox and live account as appropriate. Delayed payment methods grant
credit only after Stripe confirms payment; pending sessions grant nothing.

Send these events for your account (not connected-account events):

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`
- `charge.refunded`
- `charge.dispute.created`

Use the destination's signing secret in Supabase, not a Stripe CLI listener's
unrelated secret. The endpoint returns HTTP 500 on ledger failures so Stripe
can retry; investigate failures in Stripe delivery history and Supabase logs.
Do not display full request headers or secrets when sharing diagnostics.

## 4. Validate before live activation

With an ordinary test client, create its free survey, then choose Start New
Survey. Only the second property should show the £6 popup. Existing surveys
must remain openable and editable. The admin must remain unrestricted.

Complete a sandbox Checkout with Stripe's published test card details. Confirm:

1. Checkout displays £6 GBP once, no subscription.
2. Stripe reports successful delivery to the webhook.
3. Supabase `survey_credit_purchases` has exactly one row for the session with
   `amount_total = 600`, `currency = gbp`, and `live_mode = false`.
4. Redelivering that same event leaves one row.
5. Cancelling Checkout does not grant a credit.

**Sandbox payments deliberately do not unlock surveys on this production app.**
The return message says so. Test/live credits are separated in the database;
never flip a test purchase to live. Full free/paid redemption, concurrent requests,
rollbacks, address locks, refunds and access isolation are exercised against an
isolated PostgreSQL container by `tests/test_survey_purchases.py`; the UI and
real Supabase client are separately covered by `tests/test_client_allowance.py`.
For fully integrated sandbox redemption use a separate staging Supabase project
and a deliberate staging-only allowance policy, never alter production credits.

## 5. Activate live payments

After Stripe business verification and sandbox checks, create a **live** event
destination for the same endpoint/events. Replace the two Stripe secrets with
its live `sk_live_…` key and live destination `whsec_…` secret, then set
`SURVEY_PAYMENTS_MODE = live`. Both secrets and mode must match. Do not enable
live mode until purchase/refund information and business support details are
ready for customers.

With the business owner's authorisation, perform one real £6 purchase from a
non-admin account. Confirm the live ledger row appears once, payment return
reports a confirmed credit, one additional property can be created, and the next
new property asks for another £6. Check that a failed property insert does not
consume the credit. Confirm a refund of an unused credit revokes it. No automated
test in this repository takes real payments or proves this live setup is complete.

If the webhook arrives after the browser returns, the dashboard offers **Check
payment confirmation**. Clients should check before paying again; a success
query parameter never grants credit. Stop new payments with mode `disabled`.
While disabled, webhook processing also returns 503, so Stripe will retry pending
events; restore the matching mode/keys and inspect delivery history when resuming.
For refunds or disputes received while disabled, check delivery history and
replay failed events promptly so unused credits do not remain available.
