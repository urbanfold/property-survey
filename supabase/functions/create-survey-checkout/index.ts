import { createCheckout } from '../_shared/billing.mjs';
Deno.serve((request: Request) => createCheckout(request, { env: (name: string) => Deno.env.get(name) }));
