// Isolated audit: dummy Stripe secrets, mocked HTTP, no live purchases or webhook calls.
import assert from 'node:assert/strict';
import { createCheckout, stripeWebhook } from '../../supabase/functions/_shared/billing.mjs';
const user = '00000000-0000-4000-8000-000000000001';
const attempt = '00000000-0000-4000-8000-000000000002';
const config = {SURVEY_PAYMENTS_MODE:'test',STRIPE_SECRET_KEY:'sk_test_fixture',STRIPE_WEBHOOK_SECRET:'whsec_fixture',SUPABASE_URL:'https://fixture.test',SUPABASE_ANON_KEY:'fixture-anon',SUPABASE_SERVICE_ROLE_KEY:'fixture-service'};
const env = name => config[name];
const reply = data => new Response(JSON.stringify(data),{headers:{'content-type':'application/json'}});
let serverAmount;
const checkout = await createCheckout(new Request('https://fixture.test/checkout',{method:'POST',headers:{authorization:'Bearer fixture-session','content-type':'application/json'},body:JSON.stringify({attempt_id:attempt,amount:17900,product:'essential_feasibility'})}),{env,fetcher:async(url,options)=>{
 if(url.endsWith('/auth/v1/user'))return reply({id:user});
 if(url.includes('get_survey_allowance'))return reply({can_create:false});
 serverAmount=new URLSearchParams(options.body).get('line_items[0][price_data][unit_amount]');
 return reply({id:'cs_test_Fixture',url:'https://checkout.stripe.com/c/pay/cs_test_Fixture'});
}});
assert.equal(checkout.status,200);assert.equal(serverAmount,'600');
const calls=[];
async function event(amount,product){
 const raw=JSON.stringify({id:'evt_Fixture',type:'checkout.session.completed',livemode:false,data:{object:{id:'cs_test_Fixture',mode:'payment',payment_status:'paid',amount_total:amount,currency:'gbp',livemode:false,client_reference_id:user,payment_intent:'pi_Fixture',metadata:{product,user_id:user}}}});
 const timestamp=Math.floor(Date.now()/1000);
 const key=await crypto.subtle.importKey('raw',new TextEncoder().encode(config.STRIPE_WEBHOOK_SECRET),{name:'HMAC',hash:'SHA-256'},false,['sign']);
 const sig=await crypto.subtle.sign('HMAC',key,new TextEncoder().encode(timestamp+'.'+raw));
 return stripeWebhook(new Request('https://fixture.test/webhook',{method:'POST',headers:{'stripe-signature':`t=${timestamp},v1=${Buffer.from(sig).toString('hex')}`},body:raw}),{env,fetcher:async(url,options)=>{calls.push([url,JSON.parse(options.body)]);return reply(null);}});
}
assert.equal((await event(17900,'urbanfold_additional_survey')).status,400);assert.equal(calls.length,0);
assert.equal((await event(17900,'urbanfold_essential_feasibility')).status,200);assert.equal(calls.length,0);
assert.equal((await event(600,'urbanfold_additional_survey')).status,200);assert.equal(calls.length,1);assert.equal(calls[0][1].paid_amount,600);
console.log('PASS: browser amount £179 cannot reprice fixed £6 checkout; £179 event cannot mint survey credit; £6 signed event still records £6. Future feasibility tag is synthetic, not an implemented product.');
