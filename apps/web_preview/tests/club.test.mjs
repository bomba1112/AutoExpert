import assert from 'node:assert/strict';
import test from 'node:test';

test('the club is behind the owners_club_v1 flag and speaks three languages', async () => {
  globalThis.localStorage = {getItem: () => null, setItem() {}, removeItem() {}};
  const {createClubViews, clubCopy} = await import('../club-views.js');
  const state = {language: 'az', meta: {}};
  const views = createClubViews({root: {}, state, layout: x => x, go() {}, ensureSession: async () => {}, showToast() {}});
  assert.equal(views.enabled(), false);
  assert.equal(await views.route('club'), false);
  assert.equal(await views.vehicleRoomsButton('x'), '');
  state.meta = {owners_club_v1: {enabled: true}};
  assert.equal(views.enabled(), true);
  for (const key of ['club', 'meToo', 'report', 'rules', 'writeNote']) {
    assert.doesNotMatch(clubCopy('en', key), /[А-Яа-яЁё]/, key);
    assert.doesNotMatch(clubCopy('az', key), /[А-Яа-яЁё]/, key);
    assert.match(clubCopy('ru', key), /[А-Яа-яЁё]/, key);
  }
});
