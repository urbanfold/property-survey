import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createCheckout, stripeWebhook, verifyStripeSignature } from '../supabase/functions/_shared/billing.mjs';

const USER = '00000000-0000-4000-8000-000000000001';
const ATTEMPT = '00000000-0000-4000-8000-000000000002';
const NOW = 1800000000000;
const config = { SURVEY_PAYMENTS_MODE: 'test', STRIPE_SECRET_KEY: 'sk_test_fixture', STRIPE_WEBHOOK_SECRET: 'whsec_fixture',
  SUPABASE_URL: 'https://backend.test', SUPABASE_ANON_KEY: 'fixture-anon', SUPABASE_SERVICE_ROLE_KEY: 'fixture-service' };
const env = name => config[name];
const response = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
async function sign(raw, timestamp = Math.floor(NOW / 1000)) {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(config.STRIPE_WEBHOOK_SECRET), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const signature = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(timestamp + '.' + raw));
  return `t=${timestamp},v1=${Buffer.from(signature).toString('hex')}`;
}
function event(overrides = {}) {
  return { id: 'evt_fixture', type: 'checkout.session.completed', livemode: false, data: { object: {
    id: 'cs_test_Fixture', mode: 'payment', payment_status: 'paid', amount_total: 600, currency: 'gbp',
    livemode: false, client_reference_id: USER, payment_intent: 'pi_Fixture',
    metadata: { product: 'urbanfold_additional_survey', user_id: USER }, ...overrides } } };
}
async function webhook(value, fetcher = async () => response(null)) {
  const raw = JSON.stringify(value);
  return stripeWebhook(new Request('https://backend.test/functions/v1/stripe-survey-webhook', {
    method: 'POST', body: raw, headers: { 'stripe-signature': await sign(raw) } }), { env, fetcher, now: () => NOW });
}
function checkout(body = {}, headers = {}) {
  return new Request('https://backend.test/functions/v1/create-survey-checkout', { method: 'POST', headers: {
    origin: 'https://urbanfold.github.io', authorization: 'Bearer fixture-user-token', 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify({ attempt_id: ATTEMPT, ...body }) });
}

test('checkout authenticates the buyer, checks allowance, and fixes price/currency/return URL on the server', async () => {
  const calls = [];
  const result = await createCheckout(checkout({ amount: 1, currency: 'usd', user_id: ATTEMPT, success_url: 'https://attacker.test' }), {
    env, fetcher: async (url, options) => {
      calls.push([url, options]);
      if (url.endsWith('/auth/v1/user')) return response({ id: USER, email: 'client@example.test' });
      if (url.includes('get_survey_allowance')) return response({ can_create: false });
      const body = new URLSearchParams(options.body);
      assert.equal(body.get('line_items[0][price_data][unit_amount]'), '600');
      assert.equal(body.get('line_items[0][price_data][currency]'), 'gbp');
      assert.equal(body.get('mode'), 'payment');
      assert(![...body.keys()].some(key => key.startsWith('payment_method_types')));
      assert.equal(body.get('line_items[0][quantity]'), '1');
      assert.equal(body.get('client_reference_id'), USER);
      assert.equal(body.get('metadata[user_id]'), USER);
      assert.match(body.get('success_url'), /^https:\/\/urbanfold.github.io\/property-survey\//);
      assert.equal(options.headers['Idempotency-Key'], `urbanfold-survey-v2-${USER}-${ATTEMPT}`);
      return response({ id: 'cs_test_Fixture', url: 'https://checkout.stripe.com/c/pay/cs_test_Fixture' });
    } });
  assert.equal(result.status, 200);
  assert.equal(calls.length, 3);
  assert.equal((await result.json()).test_mode, true);
});

test('checkout blocks disabled payments, missing authentication, hostile origins, unused allowances, and unsafe Stripe responses', async () => {
  assert.equal((await createCheckout(checkout(), { env: () => undefined })).status, 503);
  assert.equal((await createCheckout(checkout({}, { authorization: '' }), { env })).status, 401);
  assert.equal((await createCheckout(checkout({}, { origin: 'https://attacker.test' }), { env })).status, 403);
  const mock = async (url) => url.endsWith('/auth/v1/user') ? response({ id: USER }) : response({ can_create: true });
  assert.equal((await createCheckout(checkout(), { env, fetcher: mock })).status, 409);
  const unsafe = async url => url.endsWith('/auth/v1/user') ? response({ id: USER }) : url.includes('get_survey_allowance')
    ? response({ can_create: false }) : response({ id: 'cs_test_Fixture', url: 'https://attacker.test' });
  assert.equal((await createCheckout(checkout(), { env, fetcher: unsafe })).status, 502);
});

test('Stripe signature checks reject tampering, stale/future requests and missing signatures, and allow secret rotation headers', async () => {
  const raw = JSON.stringify(event());
  const header = await sign(raw);
  assert(await verifyStripeSignature(raw, header, config.STRIPE_WEBHOOK_SECRET, NOW));
  assert(!await verifyStripeSignature(raw + ' ', header, config.STRIPE_WEBHOOK_SECRET, NOW));
  assert(!await verifyStripeSignature(raw, await sign(raw, NOW / 1000 - 301), config.STRIPE_WEBHOOK_SECRET, NOW));
  assert(!await verifyStripeSignature(raw, await sign(raw, NOW / 1000 + 301), config.STRIPE_WEBHOOK_SECRET, NOW));
  assert(!await verifyStripeSignature(raw, null, config.STRIPE_WEBHOOK_SECRET, NOW));
  assert(await verifyStripeSignature(raw, header + ',v1=' + '0'.repeat(64), config.STRIPE_WEBHOOK_SECRET, NOW));
});

test('only a signed, paid £6 GBP purchase grants credit to the verified session owner', async () => {
  const calls = [];
  const result = await webhook(event(), async (url, options) => { calls.push([url, JSON.parse(options.body), options.headers]); return response(null); });
  assert.equal(result.status, 200);
  assert.match(calls[0][0], /record_survey_purchase$/);
  assert.deepEqual(calls[0][1], { session_id: 'cs_test_Fixture', intent_id: 'pi_Fixture', buyer_id: USER, paid_amount: 600, paid_currency: 'gbp', is_live: false });
  assert.equal(calls[0][2].Authorization, 'Bearer fixture-service');
  for (const override of [{ amount_total: 1 }, { currency: 'usd' }, { mode: 'subscription' },
    { client_reference_id: ATTEMPT }, { payment_intent: null }, { livemode: true }]) {
    const bad = await webhook(event(override), async () => { throw Error('Must not grant credit'); });
    assert.equal(bad.status, 400);
  }
  assert.equal((await webhook(event({ payment_status: 'unpaid' }), async () => { throw Error('Must not grant'); })).status, 200);
});

test('forged browser callbacks cannot grant credit; ledger failures request webhook retry', async () => {
  const result = await stripeWebhook(new Request('https://backend.test', { method: 'POST', body: JSON.stringify(event()),
    headers: { 'stripe-signature': 't=1800000000,v1=' + '0'.repeat(64) } }), { env, now: () => NOW, fetcher: async () => { throw Error('Must not reach ledger'); } });
  assert.equal(result.status, 400);
  assert.equal((await webhook(event(), async () => response({ error: 'temporary' }, 503))).status, 500);
});

test('refunds and disputes revoke the payment intent without deleting survey data', async () => {
  for (const type of ['charge.refunded', 'charge.dispute.created']) {
    const calls = [];
    const result = await webhook({ type, livemode: false, data: { object: { payment_intent: 'pi_Fixture', amount_refunded: 600 } } }, async (url, options) => {
      calls.push([url, JSON.parse(options.body)]); return response(null);
    });
    assert.equal(result.status, 200);
    assert.match(calls[0][0], /revoke_survey_purchase$/);
    assert.equal(calls[0][1].intent_id, 'pi_Fixture');
    assert.equal(calls.length, 1);
  }
});

test('self-contained dashboard deployments register their handlers and default to disabled payments', async () => {
  const { readFile } = await import('node:fs/promises');
  const previous = globalThis.Deno;
  try {
    for (const name of ['create-survey-checkout', 'stripe-survey-webhook']) {
      let registered;
      globalThis.Deno = { env: { get: () => undefined }, serve: handler => { registered = handler; } };
      const source = await readFile(new URL('../supabase/dashboard/' + name + '.ts', import.meta.url), 'utf8');
      await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
      assert.equal(typeof registered, 'function');
      const result = await registered(new Request('https://backend.test/functions/v1/' + name, { method: 'POST', body: '{}' }));
      assert.equal(result.status, 503);
    }
  } finally {
    if (previous === undefined) delete globalThis.Deno;
    else globalThis.Deno = previous;
  }
});


test('updated Checkout request avoids a cached legacy rejection while repeated retries reuse one session', async () => {
  const oldKey = `urbanfold-survey-${USER}-${ATTEMPT}`;
  const cache = new Map([[oldKey, { error: { param: 'payment_method_types' } }]]);
  let creations = 0;
  const fetcher = async (url, options) => {
    if (url.endsWith('/auth/v1/user')) return response({ id: USER });
    if (url.includes('get_survey_allowance')) return response({ can_create: false });
    const key = options.headers['Idempotency-Key'];
    const params = new URLSearchParams(options.body);
    if ([...params.keys()].some(name => name.startsWith('payment_method_types'))) return response({ error: 'Unsupported parameter' }, 400);
    if (cache.has(key)) return response(cache.get(key), key === oldKey ? 400 : 200);
    creations++;
    const session = { id: 'cs_test_Updated', url: 'https://checkout.stripe.com/c/pay/cs_test_Updated' };
    cache.set(key, session);
    return response(session);
  };
  const first = await createCheckout(checkout(), { env, fetcher });
  const retry = await createCheckout(checkout(), { env, fetcher });
  assert.equal(first.status, 200);
  assert.equal(retry.status, 200);
  assert.deepEqual(await first.json(), await retry.json());
  assert.equal(creations, 1);
});
