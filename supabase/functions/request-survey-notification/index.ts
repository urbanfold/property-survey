import { requestSurveyNotification } from '../_shared/notifications.mjs';
Deno.serve((request: Request) => requestSurveyNotification(request, { env: (name: string) => Deno.env.get(name) }));
