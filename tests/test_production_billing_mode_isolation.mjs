import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac} from 'node:crypto';
import {createCheckout,stripeWebhook} from '../supabase/functions/_shared/billing.mjs';

const fixtures = {
  APP_URL: 'https://urbanfold.github.io/property-survey/',
  SUPABASE_URL: 'https://example.invalid',
  SUPABASE_ANON_KEY: 'fixture-anon',
  SUPABASE_SERVICE_ROLE_KEY: 'fixture-service',
  STRIPE_SECRET_KEY: 'sk_test_fixture',
  STRIPE_LIVE_SECRET_KEY: 'rk_live_fixture',
  STRIPE_WEBHOOK_SECRET: 'whsec_fixture_test',
  STRIPE_LIVE_WEBHOOK_SECRET: 'whsec_fixture_live',
};
const envFor = overrides => name => ({...fixtures,...overrides})[name];
const now = 1800000000000;
const noNetwork = async () => {assert.fail('No external call expected');};
function signedEvent(mode, secret) {
  const raw = JSON.stringify({type:'fixture.unhandled',livemode:mode==='live',data:{object:{}}});
  const t = now/1000;
  const signature = createHmac('sha256',secret).update(t+'.'+raw).digest('hex');
  return new Request('https://example.invalid/webhook',{method:'POST',headers:{'stripe-signature':'t='+t+',v1='+signature},body:raw});
}
for (const mode of ['test','live']) {
  test(mode+' accepts only its own webhook signature', async () => {
    const right = mode==='live' ? fixtures.STRIPE_LIVE_WEBHOOK_SECRET : fixtures.STRIPE_WEBHOOK_SECRET;
    const wrong = mode==='live' ? fixtures.STRIPE_WEBHOOK_SECRET : fixtures.STRIPE_LIVE_WEBHOOK_SECRET;
    const options = {env:envFor({SURVEY_PAYMENTS_MODE:mode}),fetcher:noNetwork,now:()=>now};
    assert.equal((await stripeWebhook(signedEvent(mode,right),options)).status,200);
    assert.equal((await stripeWebhook(signedEvent(mode,wrong),options)).status,400);
  });
}
test('live webhook fails closed if live secret missing despite test secret existing', async () => {
  const res=await stripeWebhook(signedEvent('live',fixtures.STRIPE_WEBHOOK_SECRET),{env:envFor({SURVEY_PAYMENTS_MODE:'live',STRIPE_LIVE_WEBHOOK_SECRET:''}),fetcher:noNetwork,now:()=>now});
  assert.equal(res.status,503);
});
const checkout = () => new Request('https://example.invalid/checkout',{method:'POST',headers:{origin:'https://urbanfold.github.io'}});
for(const overrides of [{},{SURVEY_PAYMENTS_MODE:'disabled'},{SURVEY_PAYMENTS_MODE:'live',STRIPE_LIVE_SECRET_KEY:'sk_test_fixture'},{SURVEY_PAYMENTS_MODE:'test',STRIPE_SECRET_KEY:'sk_live_fixture'}]){
  test('checkout fails closed for '+JSON.stringify(overrides),async()=>{
    assert.equal((await createCheckout(checkout(),{env:envFor(overrides),fetcher:noNetwork})).status,503);
  });
}
for(const [mode,keyName,key] of [['test','STRIPE_SECRET_KEY','rk_test_fixture'],['live','STRIPE_LIVE_SECRET_KEY','rk_live_fixture']]){
  test(mode+' restricted key still requires customer authentication',async()=>{
    assert.equal((await createCheckout(checkout(),{env:envFor({SURVEY_PAYMENTS_MODE:mode,[keyName]:key}),fetcher:noNetwork})).status,401);
  });
}
test('existing allowance prevents duplicate checkout',async()=>{
  const request=new Request('https://example.invalid/checkout',{method:'POST',headers:{origin:'https://urbanfold.github.io',authorization:'Bearer fixture'}});
  let calls=0;
  const fetcher=async url=>{
    calls++;
    if(url.endsWith('/auth/v1/user'))return Response.json({id:'12345678-1234-4234-8234-123456789abc'});
    if(url.endsWith('/rpc/get_survey_allowance'))return Response.json({can_create:true});
    assert.fail('Unexpected Stripe call');
  };
  assert.equal((await createCheckout(request,{env:envFor({SURVEY_PAYMENTS_MODE:'test'}),fetcher})).status,409);
  assert.equal(calls,2);
});
