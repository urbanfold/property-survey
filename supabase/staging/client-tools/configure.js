'use strict';
(() => {
    const STAGING_URL = 'https://hexhtduvqzleoazusskh.supabase.co';
    const status = document.getElementById('staging-config-status');
    let client;
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
            client = window.supabase.createClient(STAGING_URL, key);
            input.value = '';
            document.getElementById('staging-config').hidden = true;
            document.getElementById('staging-app').hidden = false;
            const script = document.createElement('script');
            script.src = 'app.js';
            script.onerror = () => { status.textContent = 'The app could not be loaded. Restart the local launcher.'; document.getElementById('staging-config').hidden = false; };
            document.body.appendChild(script);
        } catch (error) {
            status.textContent = error.message;
        }
    });
})();
