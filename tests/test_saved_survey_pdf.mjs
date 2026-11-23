import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import test from 'node:test';

const app = readFileSync(new URL('../app.js', import.meta.url), 'utf8');
const dashboard = app.slice(app.indexOf('async function loadDashboard()'), app.indexOf('function readableRooms('));
const download = app.slice(app.indexOf('async function downloadSavedSurveyPDF('), app.indexOf('async function downloadSurveyPack('));
const pdf = app.slice(app.indexOf('async function generatePDF('), app.indexOf('let submittingSurvey = false;'));

test('admin dashboard offers saved-survey PDF without submitting or changing it', () => {
  assert.ok(dashboard.includes('if (currentUser.email === ADMIN_EMAIL)'));
  assert.ok(dashboard.includes("pdfButton.textContent = 'Download Measurements PDF'"));
  assert.ok(dashboard.includes('downloadSavedSurveyPDF(prop.id)'));
  assert.ok(dashboard.indexOf('pdfButton.textContent') > dashboard.indexOf('if (currentUser.email === ADMIN_EMAIL)'));
  assert.doesNotMatch(dashboard, /finishSurvey\(/);
});

test('saved PDF reads the named survey with administrator and session guards', () => {
  assert.ok(download.includes('if (!currentUser || currentUser.email !== ADMIN_EMAIL) return;'));
  assert.ok(download.includes('fetchSurveySnapshot(propertyId, context)'));
  assert.ok(download.includes('await generatePDF(snapshot, context)'));
  assert.ok(download.includes('requirePrivateSession(context)'));
  assert.doesNotMatch(download, /persistSurvey|finishSurvey|submitSurvey|\.update\(|\.insert\(/);
});

test('PDF renders a provided snapshot or the existing survey submission', () => {
  assert.ok(pdf.includes('async function generatePDF(savedSurvey = null, suppliedContext = null, options = {})'));
  assert.ok(pdf.includes('const survey = savedSurvey || captureSurvey()'));
  assert.ok(pdf.includes('requirePrivateSession(context)'));
  assert.ok(pdf.includes("outputPdf('blob')"));
  assert.ok(pdf.includes('link.download = `Urbanfold_Survey_'));
});
