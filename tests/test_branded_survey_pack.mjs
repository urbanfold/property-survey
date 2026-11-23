import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import test from 'node:test';

const app = readFileSync(new URL('../app.js', import.meta.url), 'utf8');
const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const pack = app.slice(app.indexOf('async function downloadSurveyPack('), app.indexOf('async function readSurveyAllowance('));
const pdf = app.slice(app.indexOf('async function generatePDF('), app.indexOf('let submittingSurvey = false;'));

test('branded report contains logo, contacts and disclaimer', () => {
  for (const value of ['urbanfold-report-wordmark', 'urbanfold-report-mark',
    'Architectural Planning &amp; Design Services', 'survey@urbanfold.uk',
    '07762 238271', 'www.urbanfold.uk', 'not planning permission', 'pdf-photo-list']) {
    assert.ok(html.includes(value), 'Missing report element: ' + value);
  }
  assert.match(html, /urbanfold-report-disclaimer/);
  assert.match(html, /data:image\/png;base64,/);
});

test('pack is limited to the business administrator and preserves technical files', () => {
  assert.ok(pack.includes('if (!currentUser || currentUser.email !== ADMIN_EMAIL) return;'));
  assert.ok(pack.includes('fetchSurveySnapshot(propertyId, context)'));
  for (const value of ["folder.file('survey_data.txt'", "folder.file('survey_data.json'",
    "folder.file('Urbanfold_Property_Survey_Report.pdf', reportPdf)",
    "folder.file(`${group}/${path}/${i + 1}.jpg`"]) {
    assert.ok(pack.includes(value), 'Missing ZIP item: ' + value);
  }
  assert.ok(pack.includes('const reportPdf = await generatePDF(snapshot, context, { download: false, photos: pdfPhotos });'));
  assert.ok(pack.indexOf('reportPdf') < pack.indexOf('zip.generateAsync'), 'PDF must be added before ZIP compression');
  assert.doesNotMatch(pack, /persistSurvey|finishSurvey|\.update\(|\.insert\(/);
});

test('photo PDF uses authenticated photos, checks session and does not deliver incomplete ZIP', () => {
  for (const value of ['surveyPhotoEntries(survey)', 'photoDisplayUrl(item.reference)', 'await img.decode()',
    'if (!options.photos)', 'if (options.download !== false)', 'if (options.download === false) throw error',
    'requirePrivateSession(context)', 'return pdf;']) {
    assert.ok(pdf.includes(value), 'Missing PDF safeguard: ' + value);
  }
});
