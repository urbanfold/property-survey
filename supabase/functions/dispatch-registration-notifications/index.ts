import { dispatchRegistrationNotifications } from '../_shared/registration.mjs';
Deno.serve(request=>dispatchRegistrationNotifications(request,{env:name=>Deno.env.get(name)}));
