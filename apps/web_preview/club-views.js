// The owners club (product phase, stage 4): rooms by make and generation, posts, comments, photos,
// "me too" and reports. Shown only while the API advertises the owners_club_v1 flag.
import {api, apiForm, privateImageUrl} from './api.js?v=0.14.0';

const C = {
  club: ['Клуб владельцев', 'Sahiblər klubu', 'Owners club'],
  subtitle: ['Общайтесь с владельцами таких же машин', 'Eyni avtomobillərin sahibləri ilə ünsiyyət qurun', 'Talk to owners of the same car'],
  mine: ['Комнаты ваших машин', 'Avtomobillərinizin otaqları', 'Rooms for your cars'],
  noMine: ['Добавьте машину в гараж — и попадёте в её комнату.', 'Avtomobili qaraja əlavə edin — onun otağına düşəcəksiniz.', 'Add a car to your garage to join its room.'],
  makes: ['Марки', 'Markalar', 'Makes'],
  generations: ['Поколения', 'Nəsillər', 'Generations'],
  posts: ['тем', 'mövzu', 'topics'],
  newPost: ['Новая тема', 'Yeni mövzu', 'New topic'],
  title: ['Заголовок', 'Başlıq', 'Title'],
  body: ['Текст', 'Mətn', 'Text'],
  photo: ['Фото (необязательно)', 'Foto (istəyə görə)', 'Photo (optional)'],
  publish: ['Опубликовать', 'Dərc et', 'Publish'],
  comments: ['Комментарии', 'Şərhlər', 'Comments'],
  comment: ['Комментировать', 'Şərh yaz', 'Comment'],
  meToo: ['У меня то же самое', 'Məndə də eynisi', 'Me too'],
  meTooDone: ['Вы отметили: у вас то же самое', 'Qeyd etdiniz: sizdə də eynisidir', 'You marked: me too'],
  report: ['Пожаловаться', 'Şikayət et', 'Report'],
  reported: ['Жалоба отправлена модератору', 'Şikayət moderatora göndərildi', 'Report sent to a moderator'],
  writeNote: ['Чтобы писать, подтвердите почту в профиле.', 'Yazmaq üçün profildə e-poçtu təsdiqləyin.', 'Confirm your email in the profile to write.'],
  rules: ['Не публикуйте телефоны и адреса — мы скрываем их автоматически. Грубость и спам уходят на проверку модератору.', 'Telefon və ünvan dərc etməyin — onları avtomatik gizlədirik. Kobudluq və spam moderator yoxlamasına gedir.', 'Do not post phone numbers or addresses — we hide them automatically. Abuse and spam go to a moderator.'],
  displayName: ['Имя в клубе', 'Klubda ad', 'Name in the club'],
  save: ['Сохранить', 'Yadda saxla', 'Save'],
  starter: ['Из нашей базы', 'Bazamızdan', 'From our database'],
  empty: ['Пока нет тем', 'Hələ mövzu yoxdur', 'No topics yet'],
  back: ['Назад', 'Geri', 'Back'],
};
const LANG = {ru: 0, az: 1, en: 2};
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));

export function clubCopy(language, key) {
  return C[key]?.[LANG[language] ?? 0] ?? key;
}

export function createClubViews({root, state, layout, go, ensureSession, showToast}) {
  const t = key => clubCopy(state.language, key);
  const enabled = () => Boolean(state.meta?.owners_club_v1?.enabled);
  const lang = () => `language=${encodeURIComponent(state.language || 'ru')}`;

  function heading(title, subtitle, back = 'club') {
    return `<section class="page-heading"><button class="back-button" data-action="${back}" aria-label="${escape(t('back'))}">‹</button><div><h1>${escape(title)}</h1>${subtitle ? `<p>${escape(subtitle)}</p>` : ''}</div></section>`;
  }

  function roomCard(r, extra = '') {
    return `<button class="club-room-card" data-action="club-room" data-id="${escape(r.id)}"><strong>${escape(r.title)}</strong><small>${escape(extra)}</small></button>`;
  }

  async function renderHome() {
    await ensureSession();
    const data = await api(`/club/rooms?${lang()}`);
    state.clubCanWrite = data.can_write;
    root.innerHTML = layout(`
      <section class="club">
        ${heading(t('club'), t('subtitle'), 'home')}
        <section class="garage-panel"><h2>${escape(t('mine'))}</h2>
          ${data.mine.length ? `<div class="club-rooms">${data.mine.map(r => roomCard(r, [r.vehicle, r.posts != null ? `${r.posts} ${t('posts')}` : ''].filter(Boolean).join(' · '))).join('')}</div>` : `<p class="garage-empty">${escape(t('noMine'))}</p>`}
        </section>
        <section class="garage-panel"><h2>${escape(t('makes'))}</h2>
          <div class="club-rooms club-makes">${data.makes.map(r => roomCard(r, `${r.generations} · ${t('generations').toLowerCase()}`)).join('')}</div>
        </section>
        <form id="club-profile-form" class="garage-panel garage-inline">
          <label>${escape(t('displayName'))}<input name="display_name" minlength="3" maxlength="40"></label>
          <button class="button" type="submit">${escape(t('save'))}</button>
        </form>
      </section>`, {active: 'club'});
  }

  async function renderRoom(id) {
    await ensureSession();
    const room = await api(`/club/rooms/${encodeURIComponent(id)}?${lang()}`);
    state.clubRoom = room;
    root.innerHTML = layout(`
      <section class="club">
        ${heading(room.title, t('subtitle'))}
        ${room.generations?.length ? `<section class="garage-panel"><h2>${escape(t('generations'))}</h2><div class="club-rooms">${room.generations.map(g => roomCard(g)).join('')}</div></section>` : ''}
        <ul class="club-posts">${room.posts.length ? room.posts.map(postCard).join('') : `<li class="garage-empty">${escape(t('empty'))}</li>`}</ul>
        ${newPostForm()}
      </section>`, {active: 'club'});
  }

  function postCard(p) {
    return `<li class="club-post-card ${p.kind === 'STARTER' ? 'starter' : ''}" data-action="club-post" data-id="${escape(p.id)}">
      <div class="club-post-head"><strong>${escape(p.title)}</strong>${p.kind === 'STARTER' ? `<span class="garage-pill on_signal">${escape(t('starter'))}</span>` : ''}</div>
      ${p.mark ? `<small class="garage-mark">${escape(p.mark)}</small>` : ''}
      ${p.held_note ? `<small class="garage-mark">${escape(p.held_note)}</small>` : ''}
      <small class="club-meta">${escape(p.author)} · ${p.same_count} ${escape(t('meToo').toLowerCase())} · ${p.comments} ${escape(t('comments').toLowerCase())}</small>
    </li>`;
  }

  function newPostForm() {
    if (state.clubCanWrite === false) return `<p class="garage-note">${escape(t('writeNote'))}</p>`;
    return `<form id="club-post-form" class="garage-panel garage-form">
      <h2>${escape(t('newPost'))}</h2>
      <label>${escape(t('title'))}<input name="title" minlength="3" maxlength="160" required></label>
      <label>${escape(t('body'))}<textarea name="body" rows="4" maxlength="8000"></textarea></label>
      <label>${escape(t('photo'))}<input name="photo" type="file" accept="image/*"></label>
      <small>${escape(t('rules'))}</small>
      <button class="button primary" type="submit">${escape(t('publish'))}</button>
    </form>`;
  }

  async function renderPost(id) {
    await ensureSession();
    const p = await api(`/club/posts/${encodeURIComponent(id)}?${lang()}`);
    state.clubPost = p;
    root.innerHTML = layout(`
      <section class="club">
        ${heading(p.title, p.author, 'club-back-room')}
        <article class="garage-panel club-post">
          ${p.mark ? `<small class="garage-mark">${escape(p.mark)}</small>` : ''}
          ${p.held_note ? `<small class="garage-mark">${escape(p.held_note)}</small>` : ''}
          ${p.body ? `<p class="club-body">${escape(p.body).replaceAll('\n', '<br>')}</p>` : ''}
          <div class="club-photos">${p.photos.map(url => `<img alt="" data-photo="${escape(url)}">`).join('')}</div>
          <div class="garage-actions">
            <button class="button ${p.me_too ? '' : 'primary'}" data-action="club-same" ${p.me_too ? 'disabled' : ''}>${escape(p.me_too ? t('meTooDone') : t('meToo'))} · ${p.same_count}</button>
            ${p.mine || p.kind === 'STARTER' ? '' : `<button class="link-button" data-action="club-report" data-type="POST" data-id="${escape(p.id)}">${escape(t('report'))}</button>`}
          </div>
        </article>
        <section class="garage-panel">
          <h2>${escape(t('comments'))} · ${p.comments}</h2>
          <ul class="club-comments">${(p.comment_list || []).map(c => `<li><strong>${escape(c.author)}</strong>${c.held_note ? ` <small class="garage-mark">${escape(c.held_note)}</small>` : ''}<p>${escape(c.body)}</p>${c.mine ? '' : `<button class="link-button" data-action="club-report" data-type="COMMENT" data-id="${escape(c.id)}">${escape(t('report'))}</button>`}</li>`).join('')}</ul>
          ${state.clubCanWrite === false ? `<p class="garage-note">${escape(t('writeNote'))}</p>` : `<form id="club-comment-form" class="garage-inline garage-ask"><input name="body" maxlength="4000" required><button class="button" type="submit">${escape(t('comment'))}</button></form>`}
        </section>
      </section>`, {active: 'club'});
    for (const img of root.querySelectorAll('img[data-photo]')) {
      privateImageUrl(img.dataset.photo).then(url => { img.src = url; }).catch(() => img.remove());
    }
  }

  async function submit(form) {
    const data = new FormData(form);
    if (form.id === 'club-post-form') {
      const post = await api(`/club/rooms/${encodeURIComponent(state.clubRoom.id)}/posts?${lang()}`, {method: 'POST', body: JSON.stringify({title: data.get('title'), body: data.get('body') || ''})});
      const file = data.get('photo');
      if (file && file.size) {
        const upload = new FormData();
        upload.append('file', file);
        await apiForm(`/club/posts/${encodeURIComponent(post.id)}/photos`, upload);
      }
      go(`/club-post/${post.id}`);
      return true;
    }
    if (form.id === 'club-comment-form') {
      await api(`/club/posts/${encodeURIComponent(state.clubPost.id)}/comments?${lang()}`, {method: 'POST', body: JSON.stringify({body: data.get('body')})});
      await renderPost(state.clubPost.id);
      return true;
    }
    if (form.id === 'club-profile-form') {
      await api(`/club/profile?${lang()}`, {method: 'PATCH', body: JSON.stringify({display_name: data.get('display_name')})});
      showToast(t('save'));
      return true;
    }
    return false;
  }

  return {
    enabled,
    async route(name, id) {
      if (!enabled() || !['club', 'club-room', 'club-post'].includes(name)) return false;
      if (name === 'club') await renderHome();
      else if (name === 'club-room') await renderRoom(id);
      else await renderPost(id);
      return true;
    },
    async action(target) {
      const action = target.dataset.action;
      if (!action?.startsWith('club') || !enabled()) return false;
      if (action === 'club') go('/club');
      else if (action === 'club-room') go(`/club-room/${target.dataset.id}`);
      else if (action === 'club-post') go(`/club-post/${target.dataset.id}`);
      else if (action === 'club-back-room') go(state.clubPost ? `/club-room/${state.clubPost.room_id}` : '/club');
      else if (action === 'club-same') {
        await api(`/club/posts/${encodeURIComponent(state.clubPost.id)}/same?${lang()}`, {method: 'POST'});
        await renderPost(state.clubPost.id);
      } else if (action === 'club-report') {
        await api('/club/reports', {method: 'POST', body: JSON.stringify({target_type: target.dataset.type, target_id: target.dataset.id, reason: 'ABUSE'})});
        showToast(t('reported'));
      }
      return true;
    },
    submit,
    navLabel: () => t('club'),
    async vehicleRoomsButton(vehicleId) {
      if (!enabled()) return '';
      const rooms = await api(`/club/vehicles/${encodeURIComponent(vehicleId)}/rooms?${lang()}`).catch(() => []);
      if (!rooms.length) return '';
      return `<button class="button club-link" data-action="club-room" data-id="${escape(rooms[0].id)}">${escape(t('club'))}: ${escape(rooms[0].title)}</button>`;
    },
  };
}
