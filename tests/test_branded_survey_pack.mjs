import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import test from 'node:test';

const app = readFileSync(new URL('../app.js', import.meta.url), 'utf8');
const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const pack = app.slice(app.indexOf('async function downloadSurveyPack('), app.indexOf('async function readSurveyAllowance('));
const pdf = app.slice(app.indexOf('async function generatePDF('), app.indexOf('let submittingSurvey = false;'));

test('branded PDF contains Urbanfold contact information and safeguards', () => {
  for (const value of ['URBANFOLD', 'Architectural Planning &amp; Design Services', 'survey@urbanfold.uk',
    '07762 238271', 'www.urbanfold.uk', 'not planning permission', 'pdf-photo-list']) {
    assert.ok(html.includes(value), 'Missing branding element: ' + value);
  }
  assert.match(html, /urbanfold-report-wordmark/);
  assert.match(html, /urbanfold-report-disclaimer/);
});

test('saved survey pack preserves original files and embeds branded PDF and photos', () => {
  assert.match(pack, /if \(!currentUser \|\| !currentUser\) return;/);
  assert.match(pack, /fetchSurveySnapshot\(propertyId, context\)/);
  for (const text of ["folder.file('survey_data.txt'", "folder.file('survey_data.json'",
    "folder.file('Urbanfold_Property_Survey_Report.pdf', reportPdf)",
    "folder.file(`${group}/${path}/${i + 1}.jpg`"]) {
      assert.ok(pack.includes(text), 'Missing survey pack component ' + text);
  }
  assert.match(pack, /const reportPdf = await generatePDF\(snapshot, context, \{ download: false, photos: pdfPhotos \}\);/);
  assert.ok(pack.indexOf('reportPdf') < pack.indexOf("zip.generateAsync"), 'PDF must be embedded before ZIP compression');
  assert.doesNotMatch(pack, /persistSurvey|finishSurvey|\.update\(|\.insert\(/);
});

test('standalone PDF can fetch photographs but ZIP reuses bytes', () => {
  assert.match(pdf, /surveyPhotoEntries\(survey\)/);
  assert.match(pdf, /await fetch\(await photoDisplayUrl\(item.reference, context\)\)/);
  assert.match(pdf, /if \(!options.photos\)/);
  assert.match(pdf, /await img.decode\(\)/);
  assert.match(pdf, /if \(options.download !== false\)/);
  assert.match(pdf, /if \(options.download === false\) throw error/);
  assert.match(pdf, /return pdf;/);
  assert.match(pdf, /checkSession\(context\)/);
});
