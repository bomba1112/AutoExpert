import assert from 'node:assert/strict';
import test from 'node:test';

import {
  ResearchContinuation,
  executeResearchContinuation,
  useDemoPrecheck,
} from '../web_preview/research-flow.js';

const base = {
  jobId: 'job-1',
  profileId: 'profile-1',
  language: 'ru',
  vin: '3FA6P0HD0KR114795',
};

test('DeveloperMode researches the example VIN; only the separate demo flow uses precheck', () => {
  const values = {identifier: base.vin, sampleVin: base.vin,
    market: 'USA', identifierType: 'VIN', developerMode: true};
  assert.equal(useDemoPrecheck({...values, simulateUserPaywall: false}), false);
  assert.equal(useDemoPrecheck({...values, simulateUserPaywall: true}), true);
  assert.equal(useDemoPrecheck({...values, identifier: 'OTHER', simulateUserPaywall: true}), false);
});

test('DeveloperMode opens dossier without calling demo-precheck and does not retry 409', async () => {
  const paths = [];
  await assert.rejects(
    executeResearchContinuation(async (path) => {
      paths.push(path);
      const error = new Error('Conflict');
      error.status = 409;
      throw error;
    }, {...base, developerMode: true, simulateUserPaywall: false}),
    /Conflict/,
  );
  assert.deepEqual(paths, ['/research/jobs/job-1/developer-dossier']);
  assert.equal(paths.some((path) => path.includes('/demo-precheck')), false);
});

test('Simulate User Paywall calls demo-precheck exactly once', async () => {
  const calls = [];
  const continuation = await executeResearchContinuation(async (path, options) => {
    calls.push({path, options});
    return {check_id: 'check-1', details_locked: true};
  }, {...base, developerMode: true, simulateUserPaywall: true});

  assert.equal(continuation.mode, ResearchContinuation.SIMULATED_PAYWALL);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].path, '/vin/profiles/profile-1/demo-precheck');
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    language: 'ru',
    vin: '3FA6P0HD0KR114795',
  });
});
