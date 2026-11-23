import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('../app.js',import.meta.url),'utf8');
test('renderGallery ignores late private-photo URLs and errors after account changes',()=>{
  const start=source.indexOf('function renderGallery(id)');
  const end=source.indexOf('let pendingPhotoDeletions',start);
  assert(start!==-1 && end>start);
  const gallery=source.slice(start,end);
  assert.match(gallery,/const photoSession = privateSessionToken\(\)/);
  assert.match(gallery,/isPrivateSessionCurrent\(photoSession\) && image\.isConnected/);
  assert.match(gallery,/if \(!isPrivateSessionCurrent\(photoSession\)\) return/);
});
test('signed URL cache checks account generation after awaited request',()=>{
  const start=source.indexOf('async function preparePhotoLinks(');
  const end=source.indexOf('async function photoDisplayUrl(',start);
  assert(start!==-1 && end>start);
  const body=source.slice(start,end);
  assert(body.indexOf('requirePrivateSession(token)',body.indexOf('createSignedUrls'))>=0);
  assert(body.indexOf('requirePrivateSession(token)',body.indexOf('createSignedUrls'))<body.indexOf('signedPhotoUrls.set('));
});
