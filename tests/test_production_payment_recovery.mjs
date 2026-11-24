import test from 'node:test';
import assert from 'node:assert/strict';
import { recoverSurveyPayment } from '../supabase/functions/_shared/billing.mjs';

const owner = '11111111-1111-4111-8111-111111111111';
const other = '22222222-2222-4222-8222-222222222222';
const id = 'cs_live_mock123';
const metadata = { user_id: owner, product: 'urbanfold_additional_survey' };
const config = { SURVEY_PAYMENTS_MODE: 'live', STRIPE_LIVE_SECRET_KEY: 'sk_live_mock_not_real', SUPABASE_URL: 'https://mock.invalid', SUPABASE_ANON_KEY: 'mock-anon', SUPABASE_SERVICE_ROLE_KEY: 'mock-service' };
const response = (value, status = 200) => new Response(JSON.stringify(value), { status });
function fixture(opts = {}) {
  const calls = [], writes = [];
  const session = { id, livemode: true, client_reference_id: owner, metadata, mode: 'payment', status: 'complete', payment_status: 'paid', currency: 'gbp', amount_total: 600, payment_intent: 'pi_mock123', ...opts.session };
  const intent = { id: 'pi_mock123', livemode: true, status: 'succeeded', amount_received: 600, currency: 'gbp', metadata, latest_charge: 'ch_mock123', ...opts.intent };
  const charge = { id: 'ch_mock123', payment_intent: intent.id, livemode: true, paid: true, captured: true, amount: 600, currency: 'gbp', amount_refunded: 0, refunded: false, disputed: false, ...opts.charge };
  const fetcher = async (url, init = {}) => {
    const u = new URL(url); calls.push(u);
    if (u.hostname === 'mock.invalid') {
      if (u.pathname === '/auth/v1/user') return response({ id: owner }, opts.authStatus || 200);
      if (u.pathname === '/rest/v1/survey_checkout_attempts') {
        assert.equal(u.searchParams.get('user_id'), 'eq.' + owner);
        assert.equal(u.searchParams.get('live_mode'), 'eq.true');
        return response(opts.rows ?? [{ checkout_session_id: id, user_id: owner, live_mode: true }]);
      }
      if (u.pathname.startsWith('/rest/v1/rpc/')) {
        writes.push({ path: u.pathname.split('/').pop(), body: JSON.parse(init.body) });
        return response({}, opts.writeStatus || 200);
      }
    }
    if (u.hostname === 'api.stripe.com') {
      assert.equal(init.headers.Authorization, 'Bearer ' + config.STRIPE_LIVE_SECRET_KEY);
      if (opts.stripeFailure) return response({}, 503);
      if (u.pathname.startsWith('/v1/checkout/sessions/')) return response(session);
      if (u.pathname.startsWith('/v1/payment_intents/')) return response(intent);
      if (u.pathname.startsWith('/v1/charges/')) return response(charge);
    }
    throw new Error('Unexpected mocked request');
  };
  const run = (body = {}, headers = { authorization: 'Bearer mock-user' }) => recoverSurveyPayment(new Request('https://mock.invalid/recovery', { method: 'POST', headers, body: JSON.stringify(body) }), { env: key => ({ ...config, ...opts.env })[key], fetcher });
  return { run, calls, writes };
}
test('account recovery without browser reference', async () => {
  const f = fixture(); const r = await f.run(); assert.equal(r.status, 200);
  assert.equal((await r.json()).recorded, 1);
  assert.deepEqual(f.writes, [{ path: 'record_survey_purchase', body: { session_id: id, intent_id: 'pi_mock123', buyer_id: owner, paid_amount: 600, paid_currency: 'gbp', is_live: true } }]);
});
for (const [name, opts, status] of [
  ['disabled mode', { env: { SURVEY_PAYMENTS_MODE: 'disabled' } }, 503],
  ['test mode', { env: { SURVEY_PAYMENTS_MODE: 'test' } }, 503],
  ['expired authentication', { authStatus: 401 }, 401],
  ['foreign tracking record', { rows: [{ checkout_session_id: id, user_id: other, live_mode: true }] }, 503],
  ['foreign Stripe session', { session: { client_reference_id: other } }, 503],
  ['wrong product', { session: { metadata: { ...metadata, product: 'other' } } }, 503],
  ['wrong price', { session: { amount_total: 599 } }, 200],
  ['unpaid checkout', { session: { payment_status: 'unpaid' } }, 200],
  ['wrong intent owner', { intent: { metadata: { ...metadata, user_id: other } } }, 200],
  ['invalid charge', { charge: { amount: 599 } }, 503],
  ['Stripe unavailable', { stripeFailure: true }, 503],
]) test(name, async () => {
  const f = fixture(opts); assert.equal((await f.run()).status, status); assert.equal(f.writes.length, 0);
});
test('missing bearer rejected without requests', async () => {
  const f = fixture(); assert.equal((await f.run({}, {})).status, 401); assert.equal(f.calls.length, 0);
});
test('test checkout reference rejected', async () => {
  const f = fixture(); assert.equal((await f.run({ checkout_session_id: 'cs_test_mock' })).status, 400); assert.equal(f.writes.length, 0);
});
test('unknown explicit checkout rejected', async () => {
  const f = fixture({ rows: [] }); assert.equal((await f.run({ checkout_session_id: id })).status, 404); assert.equal(f.writes.length, 0);
});
for (const [name, charge, reason] of [
  ['full refund', { amount_refunded: 600, refunded: true }, 'reconciliation.refunded'],
  ['partial refund', { amount_refunded: 100 }, 'reconciliation.refunded'],
  ['dispute', { disputed: true }, 'reconciliation.disputed'],
]) test(name, async () => {
  const f = fixture({ charge }); const r = await f.run(); assert.equal(r.status, 200); assert.equal((await r.json()).ineligible, 1);
  assert.deepEqual(f.writes, [{ path: 'revoke_survey_purchase', body: { intent_id: 'pi_mock123', revocation_reason: reason } }]);
});
test('failed revocation returns error', async () => {
  const f = fixture({ charge: { disputed: true }, writeStatus: 500 }); assert.equal((await f.run()).status, 503); assert.equal(f.writes.length, 1); assert.equal(f.writes[0].path, 'revoke_survey_purchase');
});
test('failed purchase record returns error', async () => {
  const f = fixture({ writeStatus: 500 }); assert.equal((await f.run()).status, 503);
});
