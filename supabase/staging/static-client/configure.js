'use strict';
(() => {
    const STAGING_URL = 'https://hexhtduvqzleoazusskh.supabase.co';
    const status = document.getElementById('staging-config-status');
    let client;
    let checkGeneration = 0;
    const checkButton = document.getElementById('staging-isolation-check');
    const checkResult = document.getElementById('staging-isolation-result');
    checkButton.addEventListener('click', async () => {
        const generation = checkGeneration;
        checkButton.disabled = true;
        checkResult.textContent = 'Checking the database response using your signed-in staging account…';
        try {
            if (!client || new URL(client.supabaseUrl).origin !== STAGING_URL) throw Error('Stop: staging is not configured.');
            const auth = await client.auth.getUser();
            if (auth.error || !auth.data.user) throw Error('Sign in with dummy account A or B first.');
            const accounts = {
                '9036b71c-4f09-4d1b-9dce-519533c4001e': { label: 'A', own: 'f0000000-0000-4000-8000-000000000001', other: 'f0000000-0000-4000-8000-000000000002' },
                'd72b4323-d71b-4b87-b78a-09896647fddf': { label: 'B', own: 'f0000000-0000-4000-8000-000000000002', other: 'f0000000-0000-4000-8000-000000000001' }
            };
            const account = accounts[auth.data.user.id];
            if (!account) throw Error('This check requires the agreed dummy account A or B.');
            // No owner/user_id filter: the server must enforce row isolation.
            const [all, foreign] = await Promise.all([
                client.from('properties').select('id'),
                client.from('properties').select('id').eq('id', account.other)
            ]);
            const after = await client.auth.getUser();
            if (generation !== checkGeneration || after.error || after.data.user?.id !== auth.data.user.id) throw Error('The session changed. Sign in and repeat the check.');
            if (all.error || foreign.error || !Array.isArray(all.data) || !Array.isArray(foreign.data)) throw Error('The API check could not complete; no pass recorded. Check the connection and repeat.');
            const ownVisible = all.data.some(row => row.id === account.own);
            const foreignHidden = !all.data.some(row => row.id === account.other) && foreign.data.length === 0;
            const passed = ownVisible && foreignHidden;
            checkResult.textContent = `${passed ? 'PASS' : 'FAIL'} — Account ${account.label} property-read isolation\nOwn dummy property visible: ${ownVisible}\nOther dummy property hidden in unfiltered and direct reads: ${foreignHidden}\nNo records changed. This does not test writes or photographs.`;
        } catch (error) { checkResult.textContent = 'NOT VERIFIED — ' + error.message; }
        finally { checkButton.disabled = false; }
    });
    window.urbanfoldStagingClient = () => {
        if (!client) throw Error('Enter the staging public key first.');
        return client;
    };
    document.getElementById('staging-start').addEventListener('click', () => {
        const input = document.getElementById('staging-public-key');
        const key = input.value.trim();
        try {
            if (key.startsWith('sb_publishable_')) {
                if (key.length < 30) throw Error('The publishable key appears incomplete.');
            } else {
                const part = key.split('.')[1];
                if (!part) throw Error('Use the staging publishable key or legacy anon/public key.');
                const claims = JSON.parse(atob(part.replace(/-/g,'+').replace(/_/g,'/')));
                if (claims.role !== 'anon' || claims.ref !== 'hexhtduvqzleoazusskh') {
                    throw Error('This is not the staging anon/public key. Never use a secret or service-role key.');
                }
            }
            // A second boundary independent of the disabled payment UI.
            const stagingFetch = (input, init) => {
                const url = new URL(input instanceof Request ? input.url : input, location.href);
                if (url.origin !== STAGING_URL || (url.pathname.startsWith('/functions/v1/') && url.pathname !== '/functions/v1/request-survey-notification')) {
                    return Promise.reject(new Error('This staging client blocks payments and other backends.'));
                }
                return fetch(input, init);
            };
            // Preserve only routing flags before the SDK consumes the recovery URL.
            // No access/refresh token is copied into this bridge.
            const incoming = new URLSearchParams(location.hash.slice(1));
            window.urbanfoldStagingAuthReturn = new URLSearchParams();
            for (const name of ['type', 'error', 'error_code']) {
                if (incoming.has(name)) window.urbanfoldStagingAuthReturn.set(name, incoming.get(name));
            }
            client = window.supabase.createClient(STAGING_URL, key, { global: { fetch: stagingFetch } });
            client.auth.onAuthStateChange(event => {
                if (event === 'SIGNED_IN' || event === 'SIGNED_OUT') {
                    checkGeneration++;
                    checkResult.textContent = 'Sign in, then click the read-only check. Results are cleared when the account changes.';
                }
            });
            input.value = '';
            document.getElementById('staging-config').hidden = true;
            document.getElementById('staging-app').hidden = false;
            document.getElementById('staging-checks').hidden = false;
            const script = document.createElement('script');
            script.src = 'app.js';
            script.onerror = () => { status.textContent = 'The app could not be loaded. Restart the local launcher.'; document.getElementById('staging-config').hidden = false; };
            document.body.appendChild(script);
        } catch (error) {
            status.textContent = error.message;
        }
    });
})();
