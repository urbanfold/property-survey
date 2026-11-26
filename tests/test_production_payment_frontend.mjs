import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFileSync } from 'node:fs';
const source = readFileSync(new URL('../app.js', import.meta.url), 'utf8');
const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
function slice(start, end) {
  const a = source.indexOf(start), b = source.indexOf(end, a);
  assert.ok(a >= 0 && b > a);
  return source.slice(a, b);
}
const paymentCode = slice('        let checkingPurchasedCredit = false;', '        function handlePaymentReturn()');
const saveCode = slice('        async function saveDetails() {', '        const elevationsMap');
function fixture(opts = {}) {
  const calls = [], alerts = [], elements = new Map();
  const user = { id: 'customer-a', email: opts.admin ? 'admin@example.invalid' : 'a@example.invalid' };
  const allowances = [...(opts.allowances ?? [{ free_available: true, can_create: true, paid_credits: 0 }])];
  const document = { getElementById(id) {
    if (!elements.has(id)) elements.set(id, { value: id === 'detail-address' ? 'Example Street' : id === 'detail-postcode' ? 'AB1 2CD' : '', classList: { contains: () => !!opts.readonly }, hidden: true, textContent: '', disabled: false });
    return elements.get(id);
  }};
  const context = vm.createContext({
    document, currentUser: user, ADMIN_EMAIL: 'admin@example.invalid', privateSessionGeneration: 0,
    currentPropertyId: opts.existing ? 'existing-id' : null, newPropertyId: null, savingDetails: false, draftWritesEnabled: false,
    alert: message => alerts.push(message), setLoading: () => {}, saveDraft: () => calls.push('draft'), showView: view => calls.push(view),
    crypto: { randomUUID: () => 'new-id' },
    requireResult: async value => { const result = await value; if (result.error) throw result.error; return result.data; },
    sb: {
      rpc: async name => { calls.push(name); return { data: allowances.shift() ?? { free_available: false, can_create: false, paid_credits: 0 } }; },
      functions: { invoke: async (name, args) => { calls.push(name); if (opts.switchUser) { context.currentUser = { id: 'customer-b' }; context.privateSessionGeneration++; } return opts.invokeRecovery ? opts.invokeRecovery(name, args) : opts.recovery ?? { data: { checked: 1, recorded: 1 } }; } },
      from: table => {
        assert.equal(table, 'properties');
        const query = { eq: () => query, select: () => query, single: async () => opts.saveError ? { error: new Error(opts.saveError) } : { data: { id: 'saved-id' } } };
        return { update: () => { calls.push('update'); return query; }, upsert: payload => { calls.push('upsert'); assert.equal(payload.user_id, user.id); return query; } };
      }
    }
  });
  vm.runInContext('function privateSessionToken(){return {userId:currentUser?.id,generation:privateSessionGeneration}} function isPrivateSessionCurrent(t){return currentUser?.id===t.userId && privateSessionGeneration===t.generation}', context);
  vm.runInContext(paymentCode + '\n' + saveCode, context);
  return { context, calls, alerts, elements, run: code => vm.runInContext(code, context) };
}
for (const [name, opts, expected] of [
  ['free survey bypasses Stripe', {}, 'upsert'],
  ['existing survey bypasses Stripe', { existing: true }, 'update'],
  ['administrator bypasses Stripe', { admin: true }, 'upsert'],
]) test(name, async () => {
  const f = fixture(opts); await f.run('saveDetails()');
  assert.ok(f.calls.includes(expected)); assert.ok(!f.calls.includes('recover-survey-payment'));
});
test('paid survey verifies before insert', async () => {
  const f = fixture({ allowances: [{free_available:false,can_create:true},{can_create:true}] });
  await f.run('saveDetails()');
  assert.deepEqual(f.calls.slice(0,4), ['get_survey_allowance','recover-survey-payment','get_survey_allowance','upsert']);
});
for (const [name, opts] of [
  ['Stripe failure prevents save', { recovery: {error: new Error('offline')} }],
  ['account switch prevents save', { switchUser:true }],
  ['no available credit prevents save', {}],
]) test(name, async () => {
  const f = fixture({ allowances: [{free_available:false,can_create:true},{can_create:false}], ...opts });
  await f.run('saveDetails()'); assert.ok(!f.calls.includes('upsert'));
  assert.equal(f.elements.get('detail-address').value, 'Example Street');
});
test('expired verification prompts retry, not purchase', async () => {
  const f = fixture({ allowances: [{free_available:false,can_create:true},{can_create:true}], saveError:'URBANFOLD_CREDIT_REVERIFY' });
  await f.run('saveDetails()'); assert.match(f.alerts[0], /Do not pay again/);
});
test('admin customer review remains read only', async () => {
  const f = fixture({ admin:true, readonly:true }); await f.run('saveDetails()'); assert.equal(f.calls.length,0);
});
test('confirmed notice clears after redemption', async () => {
  const f = fixture({ allowances: [{paid_credits:1},{paid_credits:0}] });
  await f.run('checkPurchasedCredit()'); assert.match(f.elements.get('payment-notice').textContent,/Payment confirmed/);
  await f.run('refreshConfirmedCreditNotice()'); assert.equal(f.elements.get('payment-notice').hidden,true);
});
test('account switch cannot display old confirmation', async () => {
  const f = fixture({ switchUser:true }); await f.run('checkPurchasedCredit()');
  assert.doesNotMatch(f.elements.get('payment-notice').textContent,/Payment confirmed/);
});
test('back to dashboard reloads actual survey list', () => {
  assert.match(html,/onclick="loadDashboard\(\)">Back to Dashboard/);
});

test('paid save uses the registered recovery endpoint with mocked Stripe and Supabase', async t => {
  const owner = '11111111-1111-4111-8111-111111111111';
  const session = 'cs_live_mock';
  const intent = 'pi_mock';
  const charge = 'ch_mock';
  const metadata = { user_id: owner, product: 'urbanfold_additional_survey' };
  const env = {
    SURVEY_PAYMENTS_MODE: 'live', STRIPE_LIVE_SECRET_KEY: 'sk_live_mock_not_real',
    SUPABASE_URL: 'https://mock.invalid', SUPABASE_ANON_KEY: 'mock-anon',
    SUPABASE_SERVICE_ROLE_KEY: 'mock-service'
  };
  const responses = new Map([
    ['https://mock.invalid/auth/v1/user', { id: owner }],
    ['https://mock.invalid/rest/v1/rpc/list_recoverable_survey_sessions', [{ checkout_session_id: session, user_id: owner, live_mode: true }]],
    ['https://api.stripe.com/v1/checkout/sessions/' + session, { id: session, livemode: true, client_reference_id: owner, metadata, mode: 'payment', status: 'complete', payment_status: 'paid', currency: 'gbp', amount_total: 600, payment_intent: intent }],
    ['https://api.stripe.com/v1/payment_intents/' + intent, { id: intent, livemode: true, status: 'succeeded', amount_received: 600, currency: 'gbp', metadata, latest_charge: charge }],
    ['https://api.stripe.com/v1/charges/' + charge, { id: charge, payment_intent: intent, livemode: true, paid: true, captured: true, amount: 600, currency: 'gbp', amount_refunded: 0, refunded: false, disputed: false }],
    ['https://mock.invalid/rest/v1/rpc/record_survey_purchase', {}],
    ['https://mock.invalid/rest/v1/rpc/attest_survey_credit_verification', {}],
  ]);
  let handler, stripeUnavailable = false, attestations = 0;
  t.mock.method(globalThis, 'fetch', async url => {
    assert.ok(responses.has(url), 'Only fixture endpoints may be called');
    if (stripeUnavailable && new URL(url).hostname === 'api.stripe.com') return Response.json({}, { status: 503 });
    if (url.endsWith('/attest_survey_credit_verification')) attestations++;
    return Response.json(responses.get(url));
  });
  globalThis.Deno = { serve(fn) { handler = fn; }, env: { get: name => env[name] } };
  t.after(() => { delete globalThis.Deno; });
  await import('../supabase/functions/recover-survey-payment/index.ts');
  assert.equal(typeof handler, 'function');

  const invokeRecovery = async (route, { body }) => {
    assert.equal(route, 'recover-survey-payment');
    const response = await handler(new Request('https://mock.invalid/functions/v1/' + route, {
      method: 'POST', headers: { authorization: 'Bearer fixture-user' }, body: JSON.stringify(body)
    }));
    return response.ok ? { data: await response.json() } : { error: new Error(String(response.status)) };
  };
  const makeFixture = () => fixture({
    allowances: [{ free_available: false, can_create: true }, { can_create: true }], invokeRecovery
  });
  const success = makeFixture();
  await success.run('saveDetails()');
  assert.ok(success.calls.includes('upsert'));
  assert.equal(attestations, 1);

  stripeUnavailable = true;
  const unavailable = makeFixture();
  await unavailable.run('saveDetails()');
  assert.ok(!unavailable.calls.includes('upsert'));
  assert.equal(attestations, 1);
  assert.match(unavailable.alerts[0], /Payment verification unavailable/);
});
