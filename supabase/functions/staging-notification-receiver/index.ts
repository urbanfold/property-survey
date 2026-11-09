import { stagingNotificationReceiver } from '../_shared/staging_receiver.mjs';
Deno.serve(request => stagingNotificationReceiver(request,{env:name=>Deno.env.get(name)}));
