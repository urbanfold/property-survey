import { stripeWebhook } from '../_shared/billing.mjs';
Deno.serve((request: Request) => stripeWebhook(request, { env: (name: string) => Deno.env.get(name) }));
