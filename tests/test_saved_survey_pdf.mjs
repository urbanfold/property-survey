import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import test from 'node:test';

const app = readFileSync(new URL('../app.js', import.meta.url), 'utf8');
const dashboard = app.slice(app.indexOf('async function loadDashboard()'), app.indexOf('function readableRooms('));
const download = app.slice(app.indexOf('async function downloadSavedSurveyPDF('), app.indexOf('async function downloadSurveyPack('));
const pdf = app.slice(app.indexOf('async function generatePDF('), app.indexOf('let submittingSurvey = false;'));

test('live administrator saved-survey PDF button is admin-only and not a submit control', () => {
  assert.match(dashboard, /if \(currentUser\) \{/);
  assert.match(dashboard, /pdfButton\.textContent = 'Download Measurements PDF';/);
  assert.match(dashboard, /pdfButton\.onclick = event => \{ event\.stopPropagation\(\); downloadSavedSurveyPDF\(prop\.id\); \};/);
  assert.ok(dashboard.indexOf('pdfButton.textContent') > dashboard.indexOf('if (isStagingExportAdmin())'));
  assert.doesNotMatch(dashboard, /finishSurvey\(/);
});

test('PDF reads named survey by ID, guards session and never persists', () => {
  assert.match(download, /if \(!currentUser \|\| !currentUser\) return;/);
  assert.match(download, /fetchSurveySnapshot\(propertyId, context\)/);
  assert.match(download, /await generatePDF\(snapshot, context\)/);
  assert.match(download, /checkSession\(context\)/);
  assert.doesNotMatch(download, /persistSurvey|finishSurvey|submitSurvey|\.update\(|\.insert\(/);
});

test('PDF renderer uses snapshot when supplied and retains legacy submission export', () => {
  assert.match(pdf, /async function generatePDF\(savedSurvey = null, suppliedContext = null, options = \{\}\)/);
  assert.match(pdf, /const survey = savedSurvey \|\| captureSurvey\(\);/);
  assert.match(pdf, /checkSession\(context\)/);
  assert.match(pdf, /html2pdf\(\)/);
  assert.match(pdf, /\.outputPdf\('blob'\)/);
  assert.match(pdf, /link\.download = `Urbanfold_Survey_/);
});
