import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('../app.js',import.meta.url),'utf8');
const between=(start,end)=>{
  const i=source.indexOf(start),j=source.indexOf(end,i+start.length);
  assert(i>=0 && j>i,`Missing expected code: ${start} / ${end}`);
  return source.slice(i,j);
};

test('logout warns before signing out if device drafts may be lost',()=>{
 const body=between('async function handleLogout()','function activatePasswordRecovery(');
 assert.match(body,/saveDraft\(\)/);
 assert.match(body,/hasPrivateDeviceDrafts\(\)/);
 assert.match(body,/!confirm\(/);
 assert(body.indexOf('!confirm(')<body.indexOf('sb.auth.signOut()'));
});

test('successful logout disables draft writes before changing view and clears private data',()=>{
 const body=between('function clearSignedOutSurveyData()','async function handleLogout()');
 assert(body.indexOf('draftWritesEnabled = false')<body.indexOf("showView('view-auth')"));
 for(const item of ['currentUser = null','currentPropertyId = null','appState = { photos: {}, roomPhotos: {} }',
 'pendingPhotoDeletions = []','signedPhotoUrls.clear()','photoJobs.clear()',
 'clearPrivateDeviceDrafts()',"renderRoomsList()"])assert(body.includes(item),item);
 assert.match(body,/document\.querySelectorAll\('#view-details input/);
});

test('logout only clears survey draft keys rather than unrelated device settings',()=>{
 const body=between('function clearPrivateDeviceDrafts()','function clearSignedOutSurveyData()');
 assert.match(body,/key === 'urbanfold_draft'/);
 assert.match(body,/key\.startsWith\('urbanfold_draft_'\)/);
 assert.match(body,/localStorage\.removeItem\(key\)/);
 assert(!body.includes('localStorage.clear()'));
});

test('completed dashboard request cannot replace a newly signed-out account',()=>{
 const body=between('async function loadDashboard()','function '); // next top-level function
 assert.match(body,/const dashboardUserId = currentUser.id/);
 assert.match(body,/if \(!currentUser \|\| currentUser.id !== dashboardUserId\) return/);
 assert(body.indexOf('currentUser.id !== dashboardUserId')<body.indexOf('list.replaceChildren()'));
});
