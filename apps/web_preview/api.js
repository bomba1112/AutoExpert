const TOKEN_KEY = 'autoexpert.demo.token';
// The app's token goes in its own header: on the closed staging Authorization carries the site's
// Basic Auth, which the browser attaches by itself (a Bearer there would make it ask again).
const TOKEN_HEADER = 'X-AutoExpert-Token';
const USER_KEY = 'autoexpert.demo.user';
const SIMULATE_PAYWALL_HEADER = 'X-AutoExpert-Simulate-Paywall';

let developerMode = false;
let simulateUserPaywall = false;

function apiRoot() {
  const configured = globalThis.AUTOEXPERT_API_ROOT;
  if (typeof configured === 'string' && configured.trim()) {
    return configured.trim().replace(/\/+$/, '');
  }
  return '/api/v1';
}

function endpoint(path) {
  return `${apiRoot()}${path.startsWith('/') ? path : `/${path}`}`;
}

export function configureDeveloperAccess({enabled, simulatePaywall}) {
  developerMode = Boolean(enabled);
  simulateUserPaywall = developerMode && Boolean(simulatePaywall);
}

export class ApiError extends Error {
  constructor(status, message, payload = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

export function hasSession() {
  return Boolean(localStorage.getItem(TOKEN_KEY));
}

export function sessionUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null');
  } catch {
    return null;
  }
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export async function privateImageUrl(path) {
  const response = await fetch(endpoint(path), {headers:{[TOKEN_HEADER]: localStorage.getItem(TOKEN_KEY)||''}});
  if (!response.ok) throw new ApiError(response.status, 'ASSET_UNAVAILABLE');
  return URL.createObjectURL(await response.blob());
}

export async function createDemoSession(preferredLanguage) {
  const response = await fetch(endpoint('/auth/demo'), {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({preferred_language: preferredLanguage}),
  });
  const payload = await readPayload(response);
  if (!response.ok) {
    throw new ApiError(response.status, errorMessage(payload), payload);
  }
  localStorage.setItem(TOKEN_KEY, payload.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(payload.user));
  return payload.user;
}

export async function ensureDemoSession(preferredLanguage) {
  if (hasSession()) {
    if (developerMode) {
      const token = localStorage.getItem(TOKEN_KEY);
      let expired = true;
      try {expired = JSON.parse(atob(token.split('.')[1].replaceAll('-', '+').replaceAll('_', '/'))).exp < Date.now() / 1000 + 30;} catch {}
      if (expired) {
        const response = await fetch(endpoint('/auth/local-session/renew'), {method: 'POST', headers: {[TOKEN_HEADER]: token}});
        if (!response.ok) throw new ApiError(response.status, 'Saved local session could not be renewed');
        const payload = await response.json();
        localStorage.setItem(TOKEN_KEY, payload.access_token);
        localStorage.setItem(USER_KEY, JSON.stringify(payload.user));
      }
    }
    return sessionUser();
  }
  return createDemoSession(preferredLanguage);
}

export async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) headers.set(TOKEN_HEADER, token);
  if (developerMode && simulateUserPaywall) {
    headers.set(SIMULATE_PAYWALL_HEADER, 'true');
  }
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  let response;
  try {
    response = await fetch(endpoint(path), {...options, headers});
  } catch (error) {
    throw new ApiError(0, 'Auto Expert service is unavailable', {cause: error?.message});
  }
  const payload = await readPayload(response);
  if (!response.ok) {
    if (response.status === 401) clearSession();
    throw new ApiError(response.status, errorMessage(payload), payload);
  }
  return payload;
}

export async function downloadReportPdf(checkId, vin, buyerLanguage = null) {
  const headers = new Headers();
  headers.set(TOKEN_HEADER, localStorage.getItem(TOKEN_KEY) || '');
  if (developerMode && simulateUserPaywall) headers.set(SIMULATE_PAYWALL_HEADER, 'true');
  const path = buyerLanguage ? `/reports/buyer/${encodeURIComponent(checkId)}/pdf?language=${encodeURIComponent(buyerLanguage)}` : `/vin/${encodeURIComponent(checkId)}/report.pdf`;
  const response = await fetch(endpoint(path), {headers});
  if (!response.ok) throw new ApiError(response.status, 'PDF export unavailable');
  const blob = await response.blob();
  const filename = `AutoExpert_${vin || checkId}.pdf`;
  if (globalThis.AutoExpertFiles?.savePdf) {
    const reader = new FileReader();
    await new Promise((resolve, reject) => {
      reader.onload = () => { globalThis.AutoExpertFiles.savePdf(filename, String(reader.result).split(',')[1]); resolve(); };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  } else {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url; link.download = filename; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }
}

export async function vehiclePhotoUrl(checkId, photoId) {
  const headers = new Headers();
  headers.set(TOKEN_HEADER, localStorage.getItem(TOKEN_KEY) || '');
  if (developerMode && simulateUserPaywall) headers.set(SIMULATE_PAYWALL_HEADER, 'true');
  const response = await fetch(endpoint(`/vin/${encodeURIComponent(checkId)}/photos/${encodeURIComponent(photoId)}`), {headers});
  if (!response.ok) throw new ApiError(response.status, 'Photograph unavailable');
  return URL.createObjectURL(await response.blob());
}

export async function fetchClientConfig() {
  let response;
  try {
    response = await fetch(endpoint('/meta/client-config'));
  } catch (error) {
    throw new ApiError(0, 'Auto Expert service is unavailable', {cause: error?.message});
  }
  const payload = await readPayload(response);
  if (!response.ok) {
    throw new ApiError(response.status, errorMessage(payload), payload);
  }
  return payload;
}

export async function trackEvent(eventName, properties = {}) {
  if (!hasSession()) return;
  try {
    await api('/analytics/events', {
      method: 'POST',
      body: JSON.stringify({event_name: eventName, properties}),
    });
  } catch {
    // Analytics must never block the expert-report flow.
  }
}

async function readPayload(response) {
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) return response.json();
  const text = await response.text();
  return text ? {detail: text} : {};
}

function errorMessage(payload) {
  if (typeof payload?.detail === 'string') return payload.detail;
  if (Array.isArray(payload?.detail)) {
    return payload.detail.map((item) => item.msg || 'Validation error').join('; ');
  }
  return 'Request failed';
}

export async function downloadFile(path, filename) {
  const headers = new Headers();
  headers.set(TOKEN_HEADER, localStorage.getItem(TOKEN_KEY) || '');
  const response = await fetch(endpoint(path), {headers});
  if (!response.ok) throw new ApiError(response.status, 'Download unavailable');
  const blob = await response.blob();
  if (globalThis.AutoExpertFiles?.savePdf && blob.type === 'application/pdf') {
    const reader = new FileReader();
    await new Promise((resolve, reject) => {
      reader.onload = () => { globalThis.AutoExpertFiles.savePdf(filename, String(reader.result).split(',')[1]); resolve(); };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
    return;
  }
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url; link.download = filename; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
}

export async function apiForm(path, formData) {
  const headers = new Headers();
  headers.set(TOKEN_HEADER, localStorage.getItem(TOKEN_KEY) || '');
  const response = await fetch(endpoint(path), {method: 'POST', body: formData, headers});
  const payload = await readPayload(response);
  if (!response.ok) throw new ApiError(response.status, errorMessage(payload), payload);
  return payload;
}
