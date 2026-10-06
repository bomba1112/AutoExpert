// The subscription "my car under the expert's eye" (product phase, stage 6): plans, the price of
// the region, the trial and the store stub. Shown only while the API advertises subscription_v1;
// no real payment is taken (App Store / Google Play are connected at deployment).
import {api} from './api.js?v=0.11.0';

const C = {
  title: ['Подписка', 'Abunə', 'Subscription'],
  subtitle: ['Моя машина под присмотром эксперта', 'Avtomobilim ekspert nəzarətində', 'My car, watched by an expert'],
  free: ['Бесплатно', 'Pulsuz', 'Free'],
  premium: ['Подписка', 'Abunə', 'Subscription'],
  oneTime: ['Разово', 'Birdəfəlik', 'One-time'],
  perMonth: ['в месяц', 'ayda', 'per month'],
  current: ['Ваш план', 'Planınız', 'Your plan'],
  until: ['до', 'qədər', 'until'],
  trial: ['Попробовать бесплатно', 'Pulsuz sınayın', 'Try it free'],
  days: ['дней', 'gün', 'days'],
  appStore: ['Оформить через App Store', 'App Store ilə rəsmiləşdir', 'Subscribe with the App Store'],
  googlePlay: ['Оформить через Google Play', 'Google Play ilə rəsmiləşdir', 'Subscribe with Google Play'],
  stub: ['Предпросмотр: магазины ещё не подключены — оформление без оплаты.', 'Ön baxış: mağazalar hələ qoşulmayıb — ödənişsiz rəsmiləşdirmə.', 'Preview: the stores are not connected yet — no payment is taken.'],
  cancel: ['Отменить подписку', 'Abunəni ləğv et', 'Cancel subscription'],
  canceled: ['Отменена — действует до конца оплаченного периода', 'Ləğv edilib — ödənilmiş dövrün sonuna qədər qüvvədədir', 'Canceled — active until the end of the paid period'],
  required: ['Эта функция — по подписке', 'Bu funksiya abunə ilədir', 'This feature needs a subscription'],
  statuses: {TRIAL: ['пробный период', 'sınaq dövrü', 'trial'], ACTIVE: ['активна', 'aktivdir', 'active'], CANCELED: ['отменена', 'ləğv edilib', 'canceled']},
  locked: ['Известные проблемы вашей машины — по подписке', 'Avtomobilinizin məlum problemləri — abunə ilə', "Your car's known issues — with a subscription"],
  open: ['Подробнее о подписке', 'Abunə haqqında ətraflı', 'About the subscription'],
  back: ['Назад', 'Geri', 'Back'],
};
const LANG = {ru: 0, az: 1, en: 2};
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));

export function subscriptionCopy(language, key) {
  const entry = key.includes('.') ? key.split('.').reduce((o, k) => o?.[k], C) : C[key];
  return entry?.[LANG[language] ?? 0] ?? key;
}

export function formatPrice(price, language) {
  const locale = {ru: 'ru-RU', az: 'az-Latn-AZ', en: 'en-US'}[language] || 'en-US';
  try {
    return new Intl.NumberFormat(locale, {style: 'currency', currency: price.currency}).format(price.amount_minor / 100);
  } catch {
    return `${(price.amount_minor / 100).toFixed(2)} ${price.currency}`;
  }
}

export function createSubscriptionViews({root, state, layout, go, ensureSession, showToast}) {
  const t = key => subscriptionCopy(state.language, key);
  const enabled = () => Boolean(state.meta?.subscription_v1?.enabled);
  const lang = () => `language=${encodeURIComponent(state.language || 'ru')}`;

  async function render() {
    await ensureSession();
    const s = await api(`/subscription?${lang()}`);
    const list = items => `<ul class="sub-list">${items.map(i => `<li>${escape(i.label)}</li>`).join('')}</ul>`;
    const until = s.period_end ? new Date(s.period_end).toLocaleDateString({ru: 'ru-RU', az: 'az-Latn-AZ', en: 'en-US'}[state.language] || 'en-US') : '';
    root.innerHTML = layout(`
      <section class="garage subscription">
        <section class="page-heading"><button class="back-button" data-action="garage" aria-label="${escape(t('back'))}">‹</button><div><h1>${escape(t('title'))}</h1><p>${escape(t('subtitle'))}</p></div></section>
        ${s.tier === 'SUBSCRIPTION' ? `<p class="garage-panel sub-current"><strong>${escape(t('current'))}: ${escape(t('premium'))}</strong> · ${escape(t(`statuses.${s.status}`))} · ${escape(t('until'))} ${escape(until)}${s.status === 'CANCELED' ? `<br><small>${escape(t('canceled'))}</small>` : ''}</p>` : ''}
        <div class="sub-plans">
          <article class="garage-panel ${s.tier === 'FREE' ? 'sub-active' : ''}"><h2>${escape(t('free'))}</h2><p class="sub-price">0</p>${list(s.free)}</article>
          <article class="garage-panel sub-premium ${s.tier === 'SUBSCRIPTION' ? 'sub-active' : ''}"><h2>${escape(t('premium'))}</h2>
            <p class="sub-price">${escape(formatPrice(s.price, state.language))} <small>${escape(t('perMonth'))}</small></p>${list(s.subscription)}
            ${s.tier === 'FREE' ? `
              ${s.trial.available && s.trial.days ? `<button class="button primary" data-action="subscription-trial">${escape(t('trial'))} · ${s.trial.days} ${escape(t('days'))}</button>` : ''}
              <button class="button" data-action="subscription-buy" data-store="APP_STORE">${escape(t('appStore'))}</button>
              <button class="button" data-action="subscription-buy" data-store="GOOGLE_PLAY">${escape(t('googlePlay'))}</button>
              ${s.purchase_stub ? `<small class="garage-mark">${escape(t('stub'))}</small>` : ''}` : s.status !== 'CANCELED' ? `<button class="link-button" data-action="subscription-cancel">${escape(t('cancel'))}</button>` : ''}
          </article>
          <article class="garage-panel"><h2>${escape(t('oneTime'))}</h2>${list(s.one_time)}</article>
        </div>
      </section>`, {active: 'garage'});
  }

  return {
    enabled,
    async route(name) {
      if (!enabled() || name !== 'subscription') return false;
      await render();
      return true;
    },
    async action(target) {
      const action = target.dataset.action;
      if (!action?.startsWith('subscription') || !enabled()) return false;
      if (action === 'subscription') go('/subscription');
      else if (action === 'subscription-trial') await api(`/subscription/trial?${lang()}`, {method: 'POST'});
      else if (action === 'subscription-buy') await api(`/subscription/purchase?${lang()}`, {method: 'POST', body: JSON.stringify({store: target.dataset.store})});
      else if (action === 'subscription-cancel') await api(`/subscription/cancel?${lang()}`, {method: 'POST'});
      if (action !== 'subscription') await render();
      return true;
    },
    // a 402 from any feature: say why and open the subscription screen
    handle(error) {
      if (!enabled() || error?.status !== 402) return false;
      showToast(t('required'));
      go('/subscription');
      return true;
    },
    lockedPanel(count) {
      return `<section class="garage-panel sub-locked"><h2>${escape(t('locked'))}${count ? ` · ${count}` : ''}</h2><button class="button" data-action="subscription">${escape(t('open'))}</button></section>`;
    },
  };
}
