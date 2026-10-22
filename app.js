        const sb = window.supabase.createClient('https://arnzqizcycesukplmvuc.supabase.co', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFybnpxaXpjeWNlc3VrcGxtdnVjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTIxNTc5MTAsImV4cCI6MjEwNzczMzkxMH0.yj80dlDvAhNBBi6nTWu3bWWQMBt_ZaqmxkYKLnlnFLA');
        const ADMIN_EMAIL = 'urbanfolduk@gmail.com';
        let currentUser = null;
        let currentPropertyId = null;
        let draftWritesEnabled = true;
        let activeCloudVersion = null;
        let appState = { photos: {}, roomPhotos: {} };

        function showView(viewId) { if (viewId !== 'view-success') saveDraft(); document.querySelectorAll('.view').forEach(v => v.classList.remove('active')); document.getElementById(viewId).classList.add('active'); window.scrollTo(0, 0); const tools = document.getElementById('survey-tools'); if (tools) tools.hidden = !currentPropertyId || ['view-auth', 'view-dashboard', 'view-success'].includes(viewId); const source = document.getElementById('survey-source'); if (source) source.hidden = ['view-auth', 'view-dashboard', 'view-success'].includes(viewId); }
        function setLoading(show, text = "Processing...") { document.getElementById('loading').style.display = show ? 'flex' : 'none'; document.getElementById('loading-text').innerText = text; }

        function switchAuthTab(tab, element) {
            document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
            element.classList.add('active');
            document.getElementById('form-login').style.display = tab === 'login' ? 'block' : 'none';
            document.getElementById('form-signup').style.display = tab === 'signup' ? 'block' : 'none';
        }

        async function handleSignup() {
            const email = document.getElementById('signup-email').value.trim();
            const password = document.getElementById('signup-password').value;
            const name = document.getElementById('signup-name').value.trim();
            if (!email || !password) return alert('Please enter email and password.');
            setLoading(true, 'Creating account...');
            try {
                const data = await requireResult(sb.auth.signUp({ email, password,
                    options: { data: { full_name: name }, emailRedirectTo: new URL('.', location.href).href }
                }), 'Create account');
                if (data.session) { currentUser = data.user; await loadDashboard(); }
                else {
                    alert('Account created. Check your email to confirm, then log in.');
                    switchAuthTab('login', document.querySelector('.auth-tab'));
                    document.getElementById('login-email').value = email;
                }
            } catch (error) { alert(error.message); }
            finally { setLoading(false); }
        }

        async function handleLogin() {
            const email = document.getElementById('login-email').value.trim();
            const password = document.getElementById('login-password').value;
            if (!email || !password) return alert('Please enter email and password.');
            setLoading(true, 'Logging in...');
            try {
                const data = await requireResult(sb.auth.signInWithPassword({ email, password }), 'Log in');
                currentUser = data.user;
                document.getElementById('login-password').value = '';
                await loadDashboard();
            } catch (error) { alert(error.message); }
            finally { setLoading(false); }
        }

        async function handleLogout() {
            saveDraft();
            try {
                await requireResult(sb.auth.signOut(), 'Sign out');
                currentUser = null;
                currentPropertyId = null;
                signedPhotoUrls.clear();
                showView('view-auth');
            } catch (error) { alert(error.message); }
        }

        async function initializeApp() {
            renderRoomsList();
            try {
                const data = await requireResult(sb.auth.getSession(), 'Restore session');
                if (data.session) { currentUser = data.session.user; await loadDashboard(); }
            } catch (error) { alert('Unable to restore your login: ' + error.message); }
        }

        async function loadDashboard() {
            if (!currentUser) { showView('view-auth'); return; }
            saveDraft();
            showView('view-dashboard');
            const list = document.getElementById('dashboard-list');
            list.textContent = 'Loading surveys...';
            try {
                let query = sb.from('properties').select('*').order('created_at', { ascending: false });
                if (currentUser.email !== ADMIN_EMAIL) query = query.eq('user_id', currentUser.id);
                const data = await requireResult(query, 'Load surveys');
                list.replaceChildren();
                if (!data?.length) { list.textContent = 'No surveys yet. Start a new one above!'; return; }
                for (const prop of data) {
                    const item = document.createElement('div');
                    item.className = 'survey-item';
                    item.tabIndex = 0;
                    item.setAttribute('role', 'button');
                    item.onclick = () => resumeSurvey(prop.id);
                    item.onkeydown = event => {
                        if (event.target !== item) return;
                        if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); resumeSurvey(prop.id); }
                    };
                    const title = document.createElement('h3');
                    title.textContent = prop.address || 'Untitled Property';
                    const description = document.createElement('p');
                    description.textContent = `${prop.postcode || 'No postcode'} • ${new Date(prop.created_at).toLocaleDateString('en-GB')}`;
                    item.append(title, description);
                    if (currentUser.email === ADMIN_EMAIL) {
                        const button = document.createElement('button');
                        button.className = 'btn btn-download';
                        button.textContent = 'Download Survey Pack (ZIP)';
                        button.onclick = event => { event.stopPropagation(); downloadSurveyPack(prop.id, prop.address); };
                        item.appendChild(button);
                    }
                    list.appendChild(item);
                }
            } catch (error) { list.textContent = 'Unable to load surveys: ' + error.message; }
        }

        async function downloadSurveyPack(propertyId, address) {
            setLoading(true, 'Gathering saved survey data and photos...');
            try {
                const { snapshot } = await fetchSurveySnapshot(propertyId);
                const safeName = (address || snapshot.details.address || 'survey').replace(/[^a-z0-9]/gi, '_');
                const zip = new JSZip();
                const folder = zip.folder(safeName);
                const lines = ['URBANFOLD SURVEY REPORT', '',
                    ...Object.entries(snapshot.details).map(([key, value]) => `${key}: ${value || ''}`),
                    `Property type: ${snapshot.propType}`, '', 'EXTENSION',
                    `Types: ${snapshot.extension.types.join(', ')}`,
                    `Description: ${snapshot.extension.description || ''}`,
                    `Width: ${snapshot.extension.width ?? ''}m; length: ${snapshot.extension.length ?? ''}m`,
                    '', 'ROOMS', ...Object.entries(snapshot.rooms).map(([room, values]) => `${room}: ${JSON.stringify(values)}`)];
                folder.file('survey_data.txt', lines.join('\n'));
                folder.file('survey_data.json', JSON.stringify(snapshot, null, 2));
                for (const group of ['photos', 'roomPhotos']) {
                    for (const [label, photos] of Object.entries(snapshot.appState[group])) {
                        const path = label.replace(/[^a-z0-9-]/gi, '_');
                        for (let i = 0; i < photos.length; i++) {
                            const response = await fetch(await photoDisplayUrl(photos[i]));
                            if (!response.ok) throw new Error(`${label} photo ${i + 1} could not be downloaded (HTTP ${response.status}).`);
                            folder.file(`${group}/${path}/${i + 1}.jpg`, await response.arrayBuffer());
                        }
                    }
                }
                const blob = await zip.generateAsync({ type: 'blob' });
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = `Urbanfold_${safeName}.zip`;
                document.body.appendChild(link);
                link.click();
                setTimeout(() => { URL.revokeObjectURL(link.href); link.remove(); }, 1000);
            } catch (error) { alert('Unable to download the complete survey pack: ' + error.message); }
            finally { setLoading(false); }
        }

        function startNewSurvey() {
            if (photoJobs.size || savingProgress || submittingSurvey || savingDetails) return alert('Please wait for the current operation to finish.');
            if (confirm("This will clear your current draft. Are you sure?")) {
                localStorage.removeItem('urbanfold_draft');
                currentPropertyId = null;
                draftWritesEnabled = true;
                activeCloudVersion = null;
                document.getElementById('survey-source')?.remove();
                appState = { photos: {}, roomPhotos: {} };
                pendingPhotoDeletions = [];
                document.querySelectorAll('.preview-gallery').forEach(gallery => gallery.replaceChildren());
                document.getElementById('exterior-grid').replaceChildren();
                document.getElementById('detail-name').value = '';
                document.getElementById('detail-client-email').value = '';
                document.getElementById('detail-address').value = '';
                document.getElementById('detail-postcode').value = '';
                document.getElementById('detail-notes').value = '';
                document.getElementById('prop-type').value = '';
                document.getElementById('ext-description').value = '';
                document.getElementById('ext-width').value = '';
                document.getElementById('ext-length').value = '';
                document.querySelectorAll('input[name="ext-type"]').forEach(cb => { cb.checked = false; cb.parentElement.classList.remove('selected'); });
                roomList.forEach(room => {
                    const rid = roomId(room);
                    const shapeEl = document.getElementById(`shape-${rid}`);
                    if (shapeEl) { shapeEl.value = 'Square/Rectangular'; toggleLShapedDimensions(shapeEl); }
                    const setVal = (id) => { const el = document.getElementById(id); if (el) el.value = ''; };
                    setVal(`len-${rid}`); setVal(`wid-${rid}`); setVal(`hei-${rid}`);
                    setVal(`len1-${rid}`); setVal(`wid1-${rid}`); setVal(`len2-${rid}`); setVal(`wid2-${rid}`);
                    setVal(`len3-${rid}`); setVal(`wid3-${rid}`); setVal(`add-${rid}`);
                });
                showView('view-details');
            }
        }

        function showSurveySource(message, restoreDraft) {
            document.getElementById('survey-source')?.remove();
            const notice = document.createElement('div');
            notice.id = 'survey-source';
            notice.className = 'info-box';
            notice.textContent = message;
            if (restoreDraft) {
                const button = document.createElement('button');
                button.id = 'restore-device-draft';
                button.className = 'btn btn-secondary';
                button.textContent = 'Open draft from this device';
                button.onclick = restoreDraft;
                notice.appendChild(button);
            }
            document.querySelector('.container').prepend(notice);
        }

        const signedPhotoUrls = new Map();
        function photoLocation(reference) {
            const buckets = ['exterior-photos', 'sketch-photos', 'room-photos'];
            if (reference.startsWith('storage://')) {
                const parts = reference.slice('storage://'.length).split('/');
                const bucket = parts.shift();
                if (!buckets.includes(bucket) || !parts.length) throw new Error('Unrecognised stored photo location.');
                return { bucket, path: parts.join('/') };
            }
            const url = new URL(reference);
            if (url.origin !== new URL(sb.supabaseUrl).origin) throw new Error('Photo does not belong to this survey storage.');
            const match = url.pathname.match(/^\/storage\/v1\/object\/(?:public|sign|authenticated)\/([^/]+)\/(.+)$/);
            if (!match || !buckets.includes(match[1])) throw new Error('Unrecognised photo link.');
            return { bucket: match[1], path: decodeURIComponent(match[2]) };
        }

        async function preparePhotoLinks(snapshot) {
            const references = [...new Set(['photos', 'roomPhotos'].flatMap(group =>
                Object.values(snapshot.appState[group]).flat()))].filter(reference => !reference.startsWith('data:'));
            const groups = new Map();
            for (const reference of references) {
                if ((signedPhotoUrls.get(reference)?.expires || 0) > Date.now()) continue;
                const location = photoLocation(reference);
                const group = groups.get(location.bucket) || [];
                group.push({ reference, path: location.path });
                groups.set(location.bucket, group);
            }
            await Promise.all(Array.from(groups, async ([bucket, entries]) => {
                const data = await requireResult(sb.storage.from(bucket).createSignedUrls(entries.map(entry => entry.path), 3600), `Open private ${bucket}`);
                for (const entry of entries) {
                    const result = data?.find(item => item.path === entry.path);
                    if (!result?.signedUrl || result.error) throw new Error(`A private photo in ${bucket} could not be opened. Check its storage permissions.`);
                    signedPhotoUrls.set(entry.reference, { url: result.signedUrl, expires: Date.now() + 55 * 60 * 1000 });
                }
            }));
        }

        async function photoDisplayUrl(reference) {
            if (reference.startsWith('data:')) return reference;
            await preparePhotoLinks({ appState: { photos: { photo: [reference] }, roomPhotos: {} } });
            return signedPhotoUrls.get(reference).url;
        }

        async function fetchSurveySnapshot(id) {
                const { data, error } = await sb.from('properties').select('*').eq('id', id).single();
                if (error) throw error;
                if (!data) throw new Error('Survey could not be found.');
                const readRows = async (table) => {
                    const result = await sb.from(table).select('*').eq('property_id', id)
                        .order('created_at', { ascending: true, nullsFirst: true }).order('id', { ascending: true });
                    if (result.error) throw new Error(`${table}: ${result.error.message}`);
                    return result.data || [];
                };
                const [extensions, rooms, exterior, extensionPhotos, sketches] = await Promise.all([
                    readRows('extensions'), readRows('rooms'), readRows('exterior_photos'),
                    readRows('extension_photos'), readRows('sketch_photos')
                ]);
                let roomPhotos = [];
                if (rooms.length) {
                    const result = await sb.from('room_photos').select('*').in('room_id', rooms.map(room => room.id));
                    if (result.error) throw new Error(`room_photos: ${result.error.message}`);
                    roomPhotos = result.data || [];
                }
                const hasSubmittedData = extensions.length || rooms.length || exterior.length ||
                    extensionPhotos.length || sketches.length;
                const extension = extensions[extensions.length - 1] || {};
                const restored = {
                    propertyId: id, userId: currentUser?.id, view: 'view-details',
                    details: { name: data.surveyor_name, clientEmail: data.client_email,
                        address: data.address, postcode: data.postcode, notes: data.notes },
                    propType: data.property_type || '',
                    extension: { types: extension.extension_types || [], description: extension.description,
                        width: extension.width, length: extension.length },
                    rooms: {}, appState: { photos: {}, roomPhotos: {} }
                };
                for (const photo of exterior) {
                    const photos = restored.appState.photos[photo.elevation_type] ||= [];
                    if (!photos.includes(photo.photo_url)) photos.push(photo.photo_url);
                }
                restored.appState.photos['extension-location'] = [...new Set(extensionPhotos.map(photo => photo.photo_url))];
                restored.appState.photos.sketch = [...new Set(sketches.map(photo => photo.photo_url))];
                for (const room of rooms) {
                    const dims = room.dimensions || {};
                    restored.rooms[roomId(room.room_name)] = {
                        shape: room.shape, len: dims.l, wid: dims.w, hei: dims.h,
                        len1: dims.l1, wid1: dims.w1, len2: dims.l2, wid2: dims.w2,
                        len3: dims.l3, wid3: dims.w3, add: room.additional_measurements
                    };
                    // Include photos from earlier duplicate room rows created by the old submit flow.
                    const photos = restored.appState.roomPhotos[room.room_name] ||= [];
                    for (const photo of roomPhotos.filter(photo => photo.room_id === room.id)) {
                        if (!photos.includes(photo.photo_url)) photos.push(photo.photo_url);
                    }
                }
            await preparePhotoLinks(restored);
            return { snapshot: restored, hasCloudProgress: Boolean(hasSubmittedData) };
        }

        function surveyVersion(snapshot) {
            const canonical = value => {
                if (Array.isArray(value)) return value.map(canonical);
                if (value && typeof value === 'object') return Object.fromEntries(
                    Object.keys(value).sort().map(key => [key, canonical(value[key])]));
                return value;
            };
            return JSON.stringify(canonical({ details: snapshot.details, propType: snapshot.propType,
                extension: snapshot.extension, rooms: snapshot.rooms, appState: snapshot.appState }));
        }

        function clearCurrentDraft() {
            try {
                localStorage.removeItem(`urbanfold_draft_${currentPropertyId}`);
                const legacy = JSON.parse(localStorage.getItem('urbanfold_draft') || 'null');
                if (legacy?.propertyId === currentPropertyId) localStorage.removeItem('urbanfold_draft');
            } catch (_) { /* Verification succeeded even if browser storage is unavailable. */ }
        }

        async function resumeSurvey(id) {
            if (photoJobs.size || savingProgress || submittingSurvey || savingDetails) return alert('Please wait for the current operation to finish.');
            setLoading(true, "Opening survey...");
            draftWritesEnabled = false;
            try {
                // A draft belongs to one survey. Never apply it to another record.
                const saved = localStorage.getItem(`urbanfold_draft_${id}`) || localStorage.getItem('urbanfold_draft');
                let draft = null;
                try { draft = saved ? JSON.parse(saved) : null; } catch (_) { /* Fetch the saved property instead. */ }
                const matchingDraft = draft && draft.propertyId === id &&
                    (!draft.userId || draft.userId === currentUser?.id);
                const openDeviceDraft = () => {
                    renderRoomsList();
                    if (!loadDraft(saved)) throw new Error('Unable to display the draft.');
                    // Reopening a survey always starts at property details.
                    showView('view-details');
                    draftWritesEnabled = true;
                    activeCloudVersion = draft.baseCloudVersion || activeCloudVersion;
                    showSurveySource('Draft from this device. Changes have not been submitted.');
                };
                const { snapshot: restored, hasCloudProgress } = await fetchSurveySnapshot(id);
                activeCloudVersion = surveyVersion(restored);
                const currentDeviceEdits = matchingDraft && draft.unsaved === true && draft.baseCloudVersion === activeCloudVersion;
                if (matchingDraft && (!hasCloudProgress || currentDeviceEdits)) {
                    openDeviceDraft();
                    return;
                }
                renderRoomsList();
                if (!loadDraft(JSON.stringify(restored))) throw new Error('Unable to display this survey.');
                draftWritesEnabled = false;
                showView('view-details');
                showSurveySource(matchingDraft
                    ? 'Saved survey loaded from the database. A separate draft on this device is also available.'
                    : 'Saved survey loaded from the database.', matchingDraft ? openDeviceDraft : null);
            } catch (error) {
                alert('Unable to open survey: ' + error.message);
            } finally { setLoading(false); }
        }
        function debounce(func, wait) { let timeout; return function executedFunction(...args) { const later = () => { clearTimeout(timeout); func(...args); }; clearTimeout(timeout); timeout = setTimeout(later, wait); }; }

        function captureSurvey() {
            const draft = { propertyId: currentPropertyId, view: document.querySelector('.view.active') ? document.querySelector('.view.active').id : 'view-auth', details: { name: document.getElementById('detail-name').value, clientEmail: document.getElementById('detail-client-email').value, address: document.getElementById('detail-address').value, postcode: document.getElementById('detail-postcode').value, notes: document.getElementById('detail-notes').value }, propType: document.getElementById('prop-type').value, extension: { types: Array.from(document.querySelectorAll('input[name="ext-type"]:checked')).map(cb => cb.value), description: document.getElementById('ext-description').value, width: document.getElementById('ext-width').value, length: document.getElementById('ext-length').value }, rooms: {}, appState: appState };
            roomList.forEach(room => { const rid = roomId(room); draft.rooms[rid] = { shape: document.getElementById(`shape-${rid}`).value, len: document.getElementById(`len-${rid}`).value, wid: document.getElementById(`wid-${rid}`).value, hei: document.getElementById(`hei-${rid}`).value, len1: document.getElementById(`len1-${rid}`).value, wid1: document.getElementById(`wid1-${rid}`).value, len2: document.getElementById(`len2-${rid}`).value, wid2: document.getElementById(`wid2-${rid}`).value, len3: document.getElementById(`len3-${rid}`).value, wid3: document.getElementById(`wid3-${rid}`).value, add: document.getElementById(`add-${rid}`).value }; });
            draft.pendingPhotoDeletions = pendingPhotoDeletions;
            return draft;
        }

        function saveDraft() {
            // Login fields and an empty dashboard must not overwrite a recoverable draft.
            const activeView = document.querySelector('.view.active')?.id;
            if (!draftWritesEnabled || !currentPropertyId || !currentUser || ['view-auth', 'view-dashboard', 'view-success'].includes(activeView)) return;
            const draft = captureSurvey();
            try {
                draft.userId = currentUser.id;
                draft.unsaved = true;
                draft.baseCloudVersion = activeCloudVersion;
                draft.savedOnDeviceAt = new Date().toISOString();
                localStorage.setItem(`urbanfold_draft_${currentPropertyId}`, JSON.stringify(draft));
                localStorage.setItem('urbanfold_draft', JSON.stringify(draft));
                setSaveStatus('Draft saved on this device. Use Save progress to store it in the cloud.');
            } catch (e) { setSaveStatus('Device storage is full or unavailable. Keep this page open and save progress to the cloud now.', 'error'); }
        }

        function loadDraft(saved = localStorage.getItem('urbanfold_draft')) { if (!saved) return false;
            try { const draft = JSON.parse(saved); if (!draft) return false; currentPropertyId = draft.propertyId || null; pendingPhotoDeletions = draft.pendingPhotoDeletions || []; appState = draft.appState || { photos: {}, roomPhotos: {} }; document.querySelectorAll('.preview-gallery').forEach(gallery => { gallery.innerHTML = '<div class="empty-state">No Photos</div>'; }); if (draft.details) { document.getElementById('detail-name').value = draft.details.name || ''; document.getElementById('detail-client-email').value = draft.details.clientEmail || ''; document.getElementById('detail-address').value = draft.details.address || ''; document.getElementById('detail-postcode').value = draft.details.postcode || ''; document.getElementById('detail-notes').value = draft.details.notes || ''; } document.getElementById('prop-type').value = draft.propType || ''; document.getElementById('exterior-grid').innerHTML = ''; updateExteriorRequirements(); if (draft.extension) { document.getElementById('ext-description').value = draft.extension.description || ''; document.getElementById('ext-width').value = draft.extension.width ?? ''; document.getElementById('ext-length').value = draft.extension.length ?? ''; document.querySelectorAll('input[name="ext-type"]').forEach(cb => { cb.checked = draft.extension.types && draft.extension.types.includes(cb.value); if (cb.checked) cb.parentElement.classList.add('selected'); else cb.parentElement.classList.remove('selected'); }); } if (draft.rooms) { roomList.forEach(room => { const rid = roomId(room); const rData = draft.rooms[rid]; if (rData) { const shapeEl = document.getElementById(`shape-${rid}`); if (shapeEl) { shapeEl.value = rData.shape || 'Square/Rectangular'; toggleLShapedDimensions(shapeEl); } const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.value = val ?? ''; }; setVal(`len-${rid}`, rData.len); setVal(`wid-${rid}`, rData.wid); setVal(`hei-${rid}`, rData.hei); setVal(`len1-${rid}`, rData.len1); setVal(`wid1-${rid}`, rData.wid1); setVal(`len2-${rid}`, rData.len2); setVal(`wid2-${rid}`, rData.wid2); setVal(`len3-${rid}`, rData.len3); setVal(`wid3-${rid}`, rData.wid3); setVal(`add-${rid}`, rData.add); } }); } Object.keys(appState.photos).forEach(id => renderGallery(id)); Object.keys(appState.roomPhotos).forEach(id => renderGallery(id)); if (draft.view && document.getElementById(draft.view)) showView(draft.view); else if (currentPropertyId) showView('view-details'); return true; } catch (e) { return false; }
        }

        const enableDraftWrites = () => {
            const active = document.querySelector('.view.active')?.id;
            if (currentPropertyId && !['view-auth', 'view-dashboard', 'view-success'].includes(active)) draftWritesEnabled = true;
        };
        document.addEventListener('input', enableDraftWrites);
        document.addEventListener('change', enableDraftWrites);
        document.addEventListener('input', debounce(saveDraft, 500)); document.addEventListener('change', debounce(saveDraft, 500));
        window.addEventListener('pagehide', saveDraft);
        window.addEventListener('beforeunload', saveDraft);

        let savingDetails = false;
        async function saveDetails() {
            if (savingDetails) return;
            if (!currentUser) return alert('Please log in before saving.');
            const address = document.getElementById('detail-address').value.trim();
            const postcode = document.getElementById('detail-postcode').value.trim();
            if (!address || !postcode) return alert('Address and postcode are required.');
            savingDetails = true;
            draftWritesEnabled = true;
            setLoading(true, 'Saving property details...');
            try {
                const payload = { surveyor_name: document.getElementById('detail-name').value,
                    client_email: document.getElementById('detail-client-email').value, address, postcode,
                    notes: document.getElementById('detail-notes').value };
                const data = await requireResult(currentPropertyId
                    ? sb.from('properties').update(payload).eq('id', currentPropertyId).select().single()
                    : sb.from('properties').insert({ ...payload, user_id: currentUser.id }).select().single(), 'Save property details');
                if (!data?.id) throw new Error('The saved property could not be verified.');
                currentPropertyId = data.id;
                saveDraft();
                showView('view-type');
            } catch (error) { alert(error.message); }
            finally { savingDetails = false; setLoading(false); }
        }

        const elevationsMap = { 'terraced': ['front', 'rear', 'roof'], 'end-terraced': ['front', 'rear', 'side', 'roof'], 'semi-detached': ['front', 'rear', 'side', 'roof'], 'detached': ['front', 'rear', 'left-side', 'right-side', 'roof'], 'bungalow': ['front', 'rear', 'left-side', 'right-side', 'roof'], 'flat': ['front', 'rear', 'side'] };
        function formatElevationName(key) { return key.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '); }
        function updateExteriorRequirements() { const type = document.getElementById('prop-type').value; document.getElementById('btn-to-exterior').disabled = !type; if (type) renderExteriorGrid(type); }
        function renderExteriorGrid(type) { const grid = document.getElementById('exterior-grid'); grid.innerHTML = ''; elevationsMap[type].forEach(elev => { if (!appState.photos[elev]) appState.photos[elev] = []; const card = document.createElement('div'); card.className = 'elevation-card'; card.id = `card-${elev}`; card.innerHTML = `<h3>${formatElevationName(elev)}</h3><div class="preview-gallery" id="preview-${elev}"><div class="empty-state">No Photos</div></div><button class="camera-btn" onclick="triggerCamera('${elev}')">Take Photo</button><input type="file" accept="image/*" capture="environment" class="hidden-input" id="input-${elev}" onchange="handlePhoto('${elev}', this)">`; grid.appendChild(card); renderGallery(elev); }); }
        function triggerCamera(id) { document.getElementById(`input-${id}`).click(); }

        const photoJobs = new Set();
        async function compressImage(file) {
            if (!file.type.startsWith('image/')) throw new Error('Please choose an image file.');
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onerror = () => reject(new Error('Unable to read this photo.'));
                reader.onload = event => {
                    const img = new Image();
                    img.onerror = () => reject(new Error('This photo format could not be opened. Try a JPEG or PNG.'));
                    img.onload = () => {
                        try {
                            const scale = Math.min(1, 1200 / img.width);
                            const canvas = document.createElement('canvas');
                            canvas.width = Math.max(1, Math.round(img.width * scale));
                            canvas.height = Math.max(1, Math.round(img.height * scale));
                            canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
                            resolve(canvas.toDataURL('image/jpeg', 0.7));
                        } catch (error) { reject(error); }
                    };
                    img.src = event.target.result;
                };
                reader.readAsDataURL(file);
            });
        }

        async function handlePhoto(id, inputElement) {
            draftWritesEnabled = true;
            const state = appState;
            const propertyId = currentPropertyId;
            const files = Array.from(inputElement.files);
            inputElement.value = '';
            const job = (async () => {
                for (const file of files) {
                    const photo = await compressImage(file);
                    if (appState !== state || currentPropertyId !== propertyId) throw new Error('The survey changed while this photo was processing. Please add it again.');
                    const group = roomList.includes(id) ? state.roomPhotos : state.photos;
                    (group[id] ||= []).push(photo);
                    renderGallery(id);
                    saveDraft();
                }
            })();
            photoJobs.add(job);
            try { await job; }
            catch (error) { alert('Photo could not be added: ' + error.message); }
            finally { photoJobs.delete(job); }
        }

        function renderGallery(id) {
            const gallery = document.getElementById(`preview-${id}`);
            if (!gallery) return;
            const photos = (roomList.includes(id) ? appState.roomPhotos[id] : appState.photos[id]) || [];
            gallery.replaceChildren();
            document.getElementById(`card-${id}`)?.classList.toggle('completed', photos.length > 0);
            if (!photos.length) {
                const empty = document.createElement('div');
                empty.className = 'empty-state';
                empty.textContent = 'No Photos';
                gallery.appendChild(empty);
            }
            photos.forEach((src, index) => {
                const container = document.createElement('div');
                container.className = 'thumb-container';
                const image = document.createElement('img');
                if (src.startsWith('data:')) image.src = src;
                else {
                    photoDisplayUrl(src).then(url => { if (image.isConnected) image.src = url; })
                        .catch(error => { image.alt = 'Photo unavailable'; setSaveStatus(error.message, 'error'); });
                }
                image.alt = `${id} photo ${index + 1}`;
                const button = document.createElement('button');
                button.className = 'thumb-delete';
                button.textContent = '×';
                button.setAttribute('aria-label', `Remove ${id} photo ${index + 1}`);
                button.onclick = () => deletePhoto(id, index);
                container.append(image, button);
                gallery.appendChild(container);
            });
        }

        let pendingPhotoDeletions = [];
        function deletePhoto(id, index) {
            draftWritesEnabled = true;
            const group = roomList.includes(id) ? 'roomPhotos' : 'photos';
            const photo = appState[group][id]?.[index];
            if (!photo) return;
            if (!photo.startsWith('data:')) pendingPhotoDeletions.push({ group, id, photo });
            appState[group][id].splice(index, 1);
            renderGallery(id);
            saveDraft();
        }

        async function applyPhotoDeletions(rooms) {
            for (const deletion of pendingPhotoDeletions) {
                let operation;
                if (deletion.group === 'roomPhotos') {
                    const ids = rooms.filter(room => room.room_name === deletion.id).map(room => room.id);
                    if (!ids.length) continue;
                    operation = sb.from('room_photos').delete().in('room_id', ids).eq('photo_url', deletion.photo).select();
                } else {
                    const table = deletion.id === 'sketch' ? 'sketch_photos'
                        : deletion.id === 'extension-location' ? 'extension_photos' : 'exterior_photos';
                    operation = sb.from(table).delete().eq('property_id', currentPropertyId).eq('photo_url', deletion.photo).select();
                }
                await requireResult(operation, 'Remove saved photo');
            }
        }

        function finishExterior() { return saveCloudProgress('view-extension'); }
        function toggleCheck(element) { const cb = element.querySelector('input'); setTimeout(() => { element.classList.toggle('selected', cb.checked); saveDraft(); }, 10); }
        function finishExtension() { return saveCloudProgress('view-interior-sketch'); }
        function finishSketches() { return saveCloudProgress('view-interior-rooms'); }

        const roomList = ['Porch', 'Living Room', 'Kitchen', 'Conservatory', 'Bedroom 1', 'Bedroom 2', 'Bedroom 3', 'Bedroom 4', 'Bathroom 1', 'Bathroom 2', 'Ensuite', 'Loft Room', 'Other'];
        function roomId(name) { return name.replace(/\s+/g, '-'); }
        function toggleLShapedDimensions(selectElement) { const rid = selectElement.id.replace('shape-', ''); document.getElementById(`l-shaped-${rid}`).classList.toggle('active', selectElement.value === 'L-shaped room'); document.getElementById(`standard-${rid}`).style.display = selectElement.value === 'L-shaped room' ? 'none' : 'block'; }

        function renderRoomsList() { const list = document.getElementById('rooms-list'); list.innerHTML = ''; roomList.forEach(room => { const rid = roomId(room); if (!appState.roomPhotos[room]) appState.roomPhotos[room] = []; const acc = document.createElement('div'); acc.className = 'room-accordion'; acc.innerHTML = `<div class="room-header" onclick="this.classList.toggle('active'); this.nextElementSibling.classList.toggle('active');"><span>${room}</span><span class="arrow">▼</span></div><div class="room-body"><div class="form-group"><label>Room Shape</label><select id="shape-${rid}" onchange="toggleLShapedDimensions(this)"><option value="Square/Rectangular">Square/Rectangular</option><option value="L-shaped room">L-shaped room</option></select></div><div id="standard-${rid}" class="form-row"><div class="form-group"><label>Length (m)</label><input type="number" step="0.01" id="len-${rid}"></div><div class="form-group"><label>Width (m)</label><input type="number" step="0.01" id="wid-${rid}"></div></div><div id="l-shaped-${rid}" class="l-shaped-dimensions"><h4>L-Shaped Dimensions</h4><div class="form-row"><div class="form-group"><label>Length 1</label><input type="number" step="0.01" id="len1-${rid}"></div><div class="form-group"><label>Width 1</label><input type="number" step="0.01" id="wid1-${rid}"></div></div><div class="form-row"><div class="form-group"><label>Length 2</label><input type="number" step="0.01" id="len2-${rid}"></div><div class="form-group"><label>Width 2</label><input type="number" step="0.01" id="wid2-${rid}"></div></div><div class="form-row"><div class="form-group"><label>Length 3</label><input type="number" step="0.01" id="len3-${rid}"></div><div class="form-group"><label>Width 3</label><input type="number" step="0.01" id="wid3-${rid}"></div></div></div><div class="form-group"><label>Height (m)</label><input type="number" step="0.01" id="hei-${rid}"></div><div class="form-group"><label>Additional Measurements</label><textarea id="add-${rid}"></textarea></div><hr class="room-divider"><label style="font-weight: 500; font-size: 14px; display: block; margin-bottom: 8px;">Room Photos</label><div class="preview-gallery" id="preview-${room}"><div class="empty-state">No Photos</div></div><button class="camera-btn" onclick="triggerCamera('${room}')">Take Room Photo</button><input type="file" accept="image/*" capture="environment" class="hidden-input" id="input-${room}" onchange="handlePhoto('${room}', this)"></div>`; list.appendChild(acc); }); }

        function connectBluetooth() {
            alert('Automatic Leica measurement transfer is not implemented in this app. Please enter measurements manually. Selecting a Bluetooth device alone does not transfer measurements.');
        }

        function generatePDF() { document.getElementById('pdf-date').innerText = new Date().toLocaleDateString(); document.getElementById('pdf-address').innerText = document.getElementById('detail-address').value; document.getElementById('pdf-postcode').innerText = document.getElementById('detail-postcode').value; document.getElementById('pdf-name').innerText = document.getElementById('detail-name').value; document.getElementById('pdf-type').innerText = document.getElementById('prop-type').value; const extTypes = Array.from(document.querySelectorAll('input[name="ext-type"]:checked')).map(cb => cb.value).join(', '); document.getElementById('pdf-ext-type').innerText = extTypes || 'None'; document.getElementById('pdf-ext-dims').innerText = `${document.getElementById('ext-width').value}m x ${document.getElementById('ext-length').value}m`; document.getElementById('pdf-ext-desc').innerText = document.getElementById('ext-description').value; const roomsContainer = document.getElementById('pdf-rooms-list'); roomsContainer.innerHTML = ''; roomList.forEach(room => { const rid = roomId(room); const shape = document.getElementById(`shape-${rid}`).value; let dimsText = ''; if (shape === 'L-shaped room') { dimsText = `L-Shape: (${document.getElementById(`len1-${rid}`).value}x${document.getElementById(`wid1-${rid}`).value}), (${document.getElementById(`len2-${rid}`).value}x${document.getElementById(`wid2-${rid}`).value}), (${document.getElementById(`len3-${rid}`).value}x${document.getElementById(`wid3-${rid}`).value}), H: ${document.getElementById(`hei-${rid}`).value}m`; } else { dimsText = `L: ${document.getElementById(`len-${rid}`).value}m, W: ${document.getElementById(`wid-${rid}`).value}m, H: ${document.getElementById(`hei-${rid}`).value}m`; } if (document.getElementById(`len-${rid}`).value || document.getElementById(`len1-${rid}`).value) { roomsContainer.innerHTML += `<div class="room-item"><strong>${room}</strong> (${shape})<br>${dimsText}</div>`; } }); const element = document.getElementById('pdf-content'); element.style.display = 'block'; const opt = { margin: 1, filename: `Urbanfold_Survey_${document.getElementById('detail-postcode').value}.pdf`, image: { type: 'jpeg', quality: 0.98 }, html2canvas: { scale: 2 }, jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' } }; html2pdf().set(opt).from(element).save().then(() => { element.style.display = 'none'; }); }

        let submittingSurvey = false;

        async function requireResult(operation, label) {
            const result = await operation;
            if (result.error) throw new Error(`${label}: ${result.error.message}`);
            return result.data;
        }

        async function saveSurveyPhotos(photos, bucket, table, parent, extra = {}) {
            for (let i = 0; i < photos.length; i++) {
                // Photos loaded from Supabase already have database records.
                if (!photos[i].startsWith('data:')) continue;
                const fileName = `${currentPropertyId}/${crypto.randomUUID()}.jpg`;
                await requireResult(sb.storage.from(bucket).upload(fileName,
                    dataURLtoFile(photos[i], fileName), { contentType: 'image/jpeg' }), `Upload ${table}`);
                const reference = `storage://${bucket}/${fileName}`;
                await requireResult(sb.from(table).insert({ ...parent, ...extra, photo_url: reference }), `Save ${table}`);
                // A retry must not upload photos whose records were already saved.
                photos[i] = reference;
                saveDraft();
            }
        }

        async function persistSurvey() {
            await Promise.all(Array.from(photoJobs));
            if (!currentUser || !currentPropertyId) throw new Error('Please sign in and save property details first.');
            const expected = captureSurvey();
                const value = id => document.getElementById(id).value;
                await requireResult(sb.from('properties').update({
                    property_type: value('prop-type'), surveyor_name: value('detail-name'),
                    client_email: value('detail-client-email'), address: value('detail-address'),
                    postcode: value('detail-postcode'), notes: value('detail-notes')
                }).eq('id', currentPropertyId).select().single(), 'Save property');
                const elevations = elevationsMap[value('prop-type')] || [];
                for (const elevation of elevations) {
                    await saveSurveyPhotos(appState.photos[elevation] || [], 'exterior-photos',
                        'exterior_photos', { property_id: currentPropertyId }, { elevation_type: elevation });
                }
                const existingExtensions = await requireResult(sb.from('extensions').select('*')
                    .eq('property_id', currentPropertyId).order('created_at', { ascending: true, nullsFirst: true }).order('id', { ascending: true }), 'Read extension');
                const extension = {
                    property_id: currentPropertyId,
                    extension_types: Array.from(document.querySelectorAll('input[name="ext-type"]:checked')).map(cb => cb.value),
                    description: value('ext-description'), width: value('ext-width') || null, length: value('ext-length') || null
                };
                const existingExtension = existingExtensions?.[existingExtensions.length - 1];
                await requireResult(existingExtension
                    ? sb.from('extensions').update(extension).eq('id', existingExtension.id).select().single()
                    : sb.from('extensions').insert(extension).select().single(), 'Save extension');
                await saveSurveyPhotos(appState.photos['extension-location'] || [], 'exterior-photos',
                    'extension_photos', { property_id: currentPropertyId });
                await saveSurveyPhotos(appState.photos.sketch || [], 'sketch-photos',
                    'sketch_photos', { property_id: currentPropertyId });
                const existingRooms = await requireResult(sb.from('rooms').select('*')
                    .eq('property_id', currentPropertyId).order('created_at', { ascending: true, nullsFirst: true }).order('id', { ascending: true }), 'Read rooms');
                for (const room of roomList) {
                    const rid = roomId(room);
                    const shape = value(`shape-${rid}`);
                    const dimensions = shape === 'L-shaped room'
                        ? { l1: value(`len1-${rid}`), w1: value(`wid1-${rid}`),
                            l2: value(`len2-${rid}`), w2: value(`wid2-${rid}`),
                            l3: value(`len3-${rid}`), w3: value(`wid3-${rid}`), h: value(`hei-${rid}`) }
                        : { l: value(`len-${rid}`), w: value(`wid-${rid}`), h: value(`hei-${rid}`) };
                    const payload = { property_id: currentPropertyId, room_name: room, shape,
                        dimensions, additional_measurements: value(`add-${rid}`) };
                    const existingRoom = existingRooms?.filter(row => row.room_name === room).pop();
                    const roomData = await requireResult(existingRoom
                        ? sb.from('rooms').update(payload).eq('id', existingRoom.id).select().single()
                        : sb.from('rooms').insert(payload).select().single(), `Save room ${room}`);
                    await saveSurveyPhotos(appState.roomPhotos[room] || [], 'room-photos',
                        'room_photos', { room_id: roomData.id });
                }
            await applyPhotoDeletions(existingRooms || []);
            const { snapshot } = await fetchSurveySnapshot(currentPropertyId);
            verifySavedSurvey(expected, snapshot);
            pendingPhotoDeletions = [];
            activeCloudVersion = surveyVersion(snapshot);
            draftWritesEnabled = false;
            clearCurrentDraft();
            setSaveStatus('Progress verified in the cloud.', 'cloud');
            return snapshot;
        }

        function verifySavedSurvey(expected, actual) {
            const text = value => value == null ? '' : String(value);
            const assertSame = (left, right, label) => {
                if (text(left) !== text(right)) throw new Error(`Saved ${label} did not match. Your device draft has been kept.`);
            };
            for (const key of Object.keys(expected.details)) assertSame(expected.details[key], actual.details[key], key);
            assertSame(expected.propType, actual.propType, 'property type');
            for (const key of ['description', 'width', 'length']) assertSame(expected.extension[key], actual.extension[key], `extension ${key}`);
            if (JSON.stringify([...expected.extension.types].sort()) !== JSON.stringify([...actual.extension.types].sort()))
                throw new Error('Saved extension choices did not match.');
            for (const [id, room] of Object.entries(expected.rooms)) {
                const keys = room.shape === 'L-shaped room'
                    ? ['shape','len1','wid1','len2','wid2','len3','wid3','hei','add']
                    : ['shape','len','wid','hei','add'];
                for (const key of keys) assertSame(room[key], actual.rooms[id]?.[key], `${id} ${key}`);
            }
            for (const deletion of expected.pendingPhotoDeletions || []) {
                if ((actual.appState[deletion.group][deletion.id] || []).includes(deletion.photo))
                    throw new Error('A removed photo is still present in the cloud.');
            }
            // Uploads replace data URLs in appState with the URLs actually saved.
            for (const group of ['photos', 'roomPhotos']) {
                for (const [id, photos] of Object.entries(appState[group])) {
                    if (group === 'photos' && !['extension-location', 'sketch', ...(elevationsMap[expected.propType] || [])].includes(id)) continue;
                    const saved = new Set(actual.appState[group][id] || []);
                    if (photos.some(photo => !saved.has(photo))) throw new Error(`Not all ${id} photos could be verified.`);
                }
            }
        }

        function setSaveStatus(message, state = 'device') {
            const status = document.getElementById('save-status');
            if (status) { status.textContent = message; status.dataset.state = state; }
        }

        let savingProgress = false;
        async function saveCloudProgress(nextView) {
            if (savingProgress || submittingSurvey) return;
            savingProgress = true;
            draftWritesEnabled = true;
            saveDraft();
            setLoading(true, 'Saving and verifying your progress...');
            try {
                await persistSurvey();
                if (nextView) showView(nextView);
                setSaveStatus('Progress verified in the cloud.', 'cloud');
                showSurveySource('Progress verified in the cloud.');
            } catch (error) {
                draftWritesEnabled = true;
                saveDraft();
                setSaveStatus('Cloud save failed. Keep this page open and retry.', 'error');
                alert('Progress was not fully saved to the cloud: ' + error.message);
            } finally { savingProgress = false; setLoading(false); }
        }

        async function notifySurveySaved(snapshot) {
            const status = document.getElementById('notification-status');
            status.textContent = 'Survey data saved. Requesting the email notification...';
            const bytes = new TextEncoder().encode(JSON.stringify(snapshot));
            const digest = await crypto.subtle.digest('SHA-256', bytes);
            const signature = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
            const key = `urbanfold_notification_${currentPropertyId}_${signature}`;
            try {
                if (localStorage.getItem(key)) { status.textContent = 'An email notification was already requested for this version on this device.'; return; }
            } catch (_) { /* A storage restriction must not block a saved survey. */ }
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 15000);
            try {
                const response = await fetch('https://hooks.zapier.com/hooks/catch/29202657/410hu8q/', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, signal: controller.signal,
                    body: JSON.stringify({ client_email: snapshot.details.clientEmail, address: snapshot.details.address,
                        surveyor_name: snapshot.details.name, property_id: currentPropertyId, submission_id: signature })
                });
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                try { localStorage.setItem(key, 'requested'); } catch (_) {}
                status.textContent = 'Email notification request accepted. Check the recipient inbox.';
            } catch (error) {
                status.textContent = 'Your survey is saved, but the email request could not be confirmed. Do not resubmit just to retry email; check the inbox and automation history.';
            } finally { clearTimeout(timeout); }
        }

        async function finishSurvey() {
            if (submittingSurvey || savingProgress || savingDetails) return;
            if (!document.getElementById('detail-address').value.trim() || !document.getElementById('detail-postcode').value.trim()) {
                showView('view-details');
                return alert('Please enter the property address and postcode before submitting.');
            }
            if (!elevationsMap[document.getElementById('prop-type').value]) {
                showView('view-type');
                return alert('Please choose a property type before submitting.');
            }
            const email = document.getElementById('detail-client-email');
            if (!email.value.trim() || !email.checkValidity()) {
                showView('view-details');
                return alert('Please enter a valid client email address for the survey notification.');
            }
            if (!currentPropertyId) return alert("Property not saved. Please go back to details.");
            submittingSurvey = true;
            draftWritesEnabled = true;
            saveDraft();
            setLoading(true, "Uploading photos and saving data... This may take a minute.");
            try {
                const savedSnapshot = await persistSurvey();
                await requireResult(sb.from('properties').update({ last_submitted_at: new Date().toISOString() })
                    .eq('id', currentPropertyId).select().single(), 'Mark verified submission');
                clearCurrentDraft();
                showView('view-success');
                await notifySurveySaved(savedSnapshot);
                document.getElementById('admin-pdf-section').style.display =
                    currentUser && currentUser.email === ADMIN_EMAIL ? 'block' : 'none';
            } catch (err) {
                draftWritesEnabled = true;
                saveDraft();
                alert("Survey was not fully submitted. Your draft has been kept. " + err.message);
            } finally {
                submittingSurvey = false;
                setLoading(false);
            }
        }

        function dataURLtoFile(dataurl, filename) { let arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1], bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n); while(n--){ u8arr[n] = bstr.charCodeAt(n); } return new File([u8arr], filename, {type:mime}); }
        initializeApp();
