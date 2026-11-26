import { recoverSurveyPayment } from '../_shared/billing.mjs';

Deno.serve((request: Request) =>
  recoverSurveyPayment(request, { env: (name: string) => Deno.env.get(name) })
);
