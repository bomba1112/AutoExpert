import assert from 'node:assert/strict';
import test from 'node:test';

test('the subscription screen is behind subscription_v1, formats prices and opens on 402', async () => {
  globalThis.localStorage = {getItem: () => null, setItem() {}, removeItem() {}};
  const {createSubscriptionViews, formatPrice, subscriptionCopy} = await import('../subscription-views.js');
  let went = null;
  let toast = null;
  const state = {language: 'en', meta: {}};
  const views = createSubscriptionViews({root: {}, state, layout: x => x, go: p => { went = p; }, ensureSession: async () => {}, showToast: m => { toast = m; }});
  assert.equal(views.handle({status: 402}), false);
  assert.equal(await views.route('subscription'), false);
  state.meta = {subscription_v1: {enabled: true}};
  assert.equal(views.handle({status: 500}), false);
  assert.equal(views.handle({status: 402}), true);
  assert.equal(went, '/subscription');
  assert.equal(toast, 'This feature needs a subscription');
  assert.equal(formatPrice({amount_minor: 399, currency: 'USD'}, 'en'), '$3.99');
  assert.match(formatPrice({amount_minor: 100, currency: 'AZN'}, 'ru'), /1,00/);
  assert.equal(subscriptionCopy('az', 'statuses.TRIAL'), 'sınaq dövrü');
});
