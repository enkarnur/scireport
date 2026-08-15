/**
 * AIME page-control runtime.
 *
 * Browser iframe opens a WebSocket to /ws/page-control and handles generic
 * request/response/event envelopes. Page-control is the first channel on this
 * long-lived relay. WebSocket is the only relay transport; if it is unavailable, CLI wait/action/state fail explicitly.
 */
import { getJwtWithoutRedirect } from './auth';

type PageControlHandler = (args: any) => Promise<any> | any;
type StateProvider = () => Promise<any> | any;

interface PageControlActionMeta {
  description?: string;
  args?: Record<string, string> | null;
  display?: { zh?: string; en?: string } | null;
}

interface PageControlState {
  connected: boolean;
  transport: 'ws' | 'idle';
  sessionId: string;
  assistantId: string;
  username: string;
  lastError: string;
  actionCount: number;
}

interface PageControlGlobal {
  ready: Promise<{ ok: boolean; reason?: string; sessionId?: string; assistantId?: string; username?: string }>;
  status: () => PageControlState & { actions: number; stateProviders: number };
  registerAction: (name: string, handler: PageControlHandler, meta?: PageControlActionMeta) => void;
  unregisterAction: (name: string) => void;
  listActions: () => Array<{ name: string; description: string; args: any; display?: { zh?: string; en?: string } | null }>;
  registerStateProvider: (name: string, provider: StateProvider) => void;
  unregisterStateProvider: (name: string) => void;
}


type WSEnvelopeType = 'hello' | 'request' | 'response' | 'event' | 'error' | 'ping' | 'pong';

interface WSEnvelope<T = any> {
  type: WSEnvelopeType | string;
  id?: string;
  channel?: string;
  method?: string;
  event?: string;
  ok?: boolean;
  payload?: T;
  error?: string;
  t?: number;
}

const WS_CHANNEL_PAGE_CONTROL = 'page-control';
const WS_METHOD_PAGE_ACTION = 'page.action';
const WS_METHOD_PAGE_DESCRIBE = 'page.describe';
const WS_METHOD_PAGE_STATE = 'page.state';

declare global {
  interface Window {
    __pageControlLoaded__?: boolean;
    __pageControlInit__?: boolean;
    __pageControlInitTime__?: number;
    pageControl?: PageControlGlobal;
  }
}

const DEBUG = false;
const log = (...a: any[]) => {
  if (DEBUG) console.debug('[page-control]', ...a);
};
const warn = (...a: any[]) => console.warn('[page-control]', ...a);

async function fetchJwt(): Promise<string | undefined> {
  try {
    return await getJwtWithoutRedirect();
  } catch (e) {
    warn('getJwt failed', e);
    return undefined;
  }
}

async function authHeaders(): Promise<Record<string, string>> {
  const jwt = await fetchJwt();
  return jwt ? { Authorization: `Byte-Cloud-JWT ${jwt}` } : {};
}

function detectEnv(): { inIframe: boolean; nested: boolean } {
  const inIframe = window.self !== window.top;
  let nested = false;
  try {
    nested = inIframe && window.parent !== window.top;
  } catch {
    nested = true;
  }
  return { inIframe, nested };
}

async function fetchAimeConfig(): Promise<{ assistant_id?: string; username?: string; session_id?: string } | null> {
  try {
    const extra = await authHeaders();
    const resp = await fetch('/api/aime/config', {
      credentials: 'include',
      headers: { Accept: 'application/json', ...extra },
    });
    if (!resp.ok) return null;
    return await resp.json();
  } catch (e) {
    warn('aime config error', e);
    return null;
  }
}

const actions = new Map<
  string,
  { handler: PageControlHandler; description: string; args: any; display: { zh?: string; en?: string } | null }
>();
const stateProviders = new Map<string, StateProvider>();

function registerAction(name: string, handler: PageControlHandler, meta?: PageControlActionMeta) {
  if (!name) throw new Error('action name required');
  if (typeof handler !== 'function') throw new Error('handler must be function');
  actions.set(name, {
    handler,
    description: meta?.description || '',
    args: meta?.args ?? null,
    display: meta?.display ?? null,
  });
}

function unregisterAction(name: string) {
  actions.delete(name);
}

function listActions() {
  return Array.from(actions.entries()).map(([name, m]) => ({
    name,
    description: m.description,
    args: m.args,
    display: m.display,
  }));
}

function registerStateProvider(name: string, provider: StateProvider) {
  if (!name) throw new Error('state provider name required');
  if (typeof provider !== 'function') throw new Error('state provider must be function');
  stateProviders.set(name, provider);
}

function unregisterStateProvider(name: string) {
  stateProviders.delete(name);
}

function qs(selector: string): Element | null {
  if (!selector) throw new Error('selector required');
  return document.querySelector(selector);
}

function isVisible(el: Element | null): boolean {
  if (!el) return false;
  const he = el as HTMLElement;
  if (!he.isConnected) return false;
  const rects = he.getClientRects();
  if (!rects || rects.length === 0) return false;
  const style = window.getComputedStyle(he);
  if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0) return false;
  return true;
}

function visibleText(el: Element | null): string {
  if (!el) return '';
  const he = el as HTMLElement;
  return (he.innerText || he.textContent || '').replace(/\s+/g, ' ').trim();
}

function summarizeElement(el: Element) {
  const he = el as HTMLElement;
  const input = el as HTMLInputElement;
  const dataset: Record<string, string> = {};
  const anyEl = el as any;
  if (anyEl.dataset) {
    for (const k of Object.keys(anyEl.dataset)) {
      const v = anyEl.dataset[k];
      if (typeof v === 'string' && v.length <= 120) dataset[k] = v;
    }
  }
  return {
    tag: el.tagName.toLowerCase(),
    testid: he.getAttribute('data-testid') || null,
    id: el.id || null,
    name: el.getAttribute('name') || null,
    type: el.getAttribute('type') || null,
    role: el.getAttribute('role') || null,
    aria: el.getAttribute('aria-label') || null,
    placeholder: el.getAttribute('placeholder') || null,
    value: 'value' in input ? String(input.value ?? '').slice(0, 160) : null,
    checked: typeof input.checked === 'boolean' ? input.checked : null,
    disabled: typeof input.disabled === 'boolean' ? input.disabled : null,
    visible: isVisible(el),
    text: visibleText(el).slice(0, 160),
    dataset: Object.keys(dataset).length ? dataset : null,
  };
}

function findByText(text: string, opts?: { selector?: string; exact?: boolean }): HTMLElement | null {
  const needle = String(text || '').trim();
  if (!needle) throw new Error('text required');
  const scope = opts?.selector || 'button,a,[role="button"],[role="tab"],label,span,div,li,td,th,option';
  const exact = !!opts?.exact;
  const candidates = (Array.from(document.querySelectorAll(scope)) as HTMLElement[])
    .filter((el) => isVisible(el))
    .map((el) => ({ el, txt: visibleText(el) }))
    .filter(({ txt }) => (exact ? txt === needle : txt.includes(needle)))
    .sort((a, b) => a.txt.length - b.txt.length);
  return candidates.length ? candidates[0].el : null;
}

async function readCustomState() {
  const custom: Record<string, any> = {};
  for (const [name, provider] of stateProviders.entries()) {
    try {
      custom[name] = await provider();
    } catch (e: any) {
      custom[name] = { ok: false, error: e?.message || String(e) };
    }
  }
  return custom;
}

registerAction('__describe__', async () => ({ plugin: 'aime-app', actions: listActions(), stateProviders: Array.from(stateProviders.keys()) }), {
  description: 'List all available page-control actions and state providers',
});

registerAction(
  '__state__',
  async () => {
    const active = document.activeElement as HTMLElement | null;
    const testidNodes = Array.from(document.querySelectorAll('[data-testid]')).slice(0, 120);
    return {
      url: location.href,
      pathname: location.pathname,
      hash: location.hash,
      title: document.title,
      viewport: { w: innerWidth, h: innerHeight },
      active_element: active
        ? { tag: active.tagName, testid: active.getAttribute('data-testid') || null, id: active.id || null, cls: active.className || null }
        : null,
      landmarks: Array.from(document.querySelectorAll('h1,h2,h3,[role="heading"],[aria-label]'))
        .slice(0, 40)
        .map((el) => ({ tag: el.tagName.toLowerCase(), text: visibleText(el).slice(0, 120), aria: el.getAttribute('aria-label') || null })),
      testids: testidNodes.map((el) => summarizeElement(el)),
      body_text_head: (document.body?.innerText || '').slice(0, 500),
      custom: await readCustomState(),
    };
  },
  { description: 'Return a generic page snapshot: URL/title/viewport/active element/landmarks/data-testid elements/custom state', display: { zh: '正在查看页面状态', en: 'Checking page state' } },
);

registerAction(
  '__control_start__',
  async ({ display }: { display?: { zh?: string; en?: string } }) => {
    explicitControlActive = true;
    markControlStart(display || { zh: '正在操作应用', en: 'Operating app' });
    return { ok: true, active: true };
  },
  { description: 'Show the session-level controlling banner before API or DOM operations', args: { display: '{zh,en}?' }, display: { zh: '正在操作应用', en: 'Operating app' } },
);

registerAction('__control_end__', async () => {
  explicitControlActive = false;
  clearControllingAfterDelay();
  return { ok: true, clearing_after_ms: CONTROL_END_DELAY_MS };
}, { description: 'Clear the session-level controlling banner state after the default 2.5s completion delay' });

registerAction('dom.click', async ({ selector }: { selector: string }) => {
  const el = qs(selector) as HTMLElement | null;
  if (!el) throw new Error('element not found: ' + selector);
  el.scrollIntoView({ block: 'center', inline: 'center' });
  el.click();
  return { clicked: selector };
}, { description: 'Click the first element matching the selector', args: { selector: 'string' }, display: { zh: '点击页面元素', en: 'Clicking element' } });

registerAction('dom.fill', async ({ selector, value }: { selector: string; value: string }) => {
  const el = qs(selector) as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement | null;
  if (!el) throw new Error('element not found: ' + selector);
  if (!('value' in el)) throw new Error('element has no value: ' + selector);
  const proto = el instanceof HTMLSelectElement ? HTMLSelectElement.prototype : el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, 'value')?.set?.call(el, value === null || value === undefined ? '' : String(value));
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
  return { filled: selector };
}, { description: 'Fill input/textarea/select via native setter and dispatch input+change events', args: { selector: 'string', value: 'string' }, display: { zh: '填写输入框', en: 'Filling input' } });

registerAction('dom.text', async ({ selector }: { selector: string }) => {
  const el = qs(selector);
  if (!el) throw new Error('element not found: ' + selector);
  return { text: (el.textContent || '').trim() };
}, { description: 'Read element text content', args: { selector: 'string' }, display: { zh: '正在读取文本', en: 'Reading text' } });

registerAction('dom.exists', async ({ selector }: { selector: string }) => ({ exists: !!document.querySelector(selector) }), {
  description: 'Check whether the element exists', args: { selector: 'string' }, display: { zh: '正在检测元素', en: 'Checking element' },
});


registerAction('dom.value', async ({ selector }: { selector: string }) => {
  const el = qs(selector) as HTMLElement | null;
  if (!el) throw new Error('element not found: ' + selector);
  const input = el as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;
  const selectedOptions = el instanceof HTMLSelectElement
    ? Array.from(el.selectedOptions).map((o) => ({ value: o.value, label: (o.textContent || '').trim() }))
    : null;
  return {
    selector,
    tag: el.tagName.toLowerCase(),
    value: 'value' in input ? String(input.value ?? '') : null,
    text: visibleText(el),
    checked: typeof (input as HTMLInputElement).checked === 'boolean' ? (input as HTMLInputElement).checked : null,
    selected_options: selectedOptions,
    disabled: typeof (input as HTMLInputElement).disabled === 'boolean' ? (input as HTMLInputElement).disabled : null,
    visible: isVisible(el),
  };
}, { description: 'Read current value/text/checked state for an input-like element', args: { selector: 'string' }, display: { zh: '正在读取控件值', en: 'Reading value' } });

registerAction('dom.focus', async ({ selector }: { selector: string }) => {
  const el = qs(selector) as HTMLElement | null;
  if (!el) throw new Error('element not found: ' + selector);
  el.scrollIntoView({ block: 'center', inline: 'center' });
  el.focus({ preventScroll: true });
  const active = document.activeElement as HTMLElement | null;
  return {
    focused: selector,
    active: active ? { tag: active.tagName.toLowerCase(), testid: active.getAttribute('data-testid') || null, id: active.id || null } : null,
  };
}, { description: 'Focus an element, scrolling it into view first', args: { selector: 'string' }, display: { zh: '聚焦元素', en: 'Focusing element' } });

registerAction('dom.press', async ({ selector, key, code, ctrlKey, metaKey, shiftKey, altKey }: { selector?: string; key: string; code?: string; ctrlKey?: boolean; metaKey?: boolean; shiftKey?: boolean; altKey?: boolean }) => {
  if (!key) throw new Error('key required');
  const target = (selector ? qs(selector) : document.activeElement) as HTMLElement | null;
  const el = target || document.body;
  if (selector && !target) throw new Error('element not found: ' + selector);
  if (selector && typeof el.focus === 'function') {
    el.scrollIntoView({ block: 'center', inline: 'center' });
    el.focus({ preventScroll: true });
  }
  const eventInit: KeyboardEventInit = {
    key,
    code: code || key,
    bubbles: true,
    cancelable: true,
    ctrlKey: !!ctrlKey,
    metaKey: !!metaKey,
    shiftKey: !!shiftKey,
    altKey: !!altKey,
  };
  const down = new KeyboardEvent('keydown', eventInit);
  const downOk = el.dispatchEvent(down);
  const shouldKeyPress = key.length === 1 || key === 'Enter';
  const pressOk = shouldKeyPress ? el.dispatchEvent(new KeyboardEvent('keypress', eventInit)) : true;
  const upOk = el.dispatchEvent(new KeyboardEvent('keyup', eventInit));
  return { pressed: key, selector: selector || null, default_prevented: !downOk || !pressOk || !upOk };
}, { description: 'Dispatch keydown/keypress/keyup to a focused element or the current active element', args: { selector: 'string?', key: 'string', code: 'string?', ctrlKey: 'boolean?', metaKey: 'boolean?', shiftKey: 'boolean?', altKey: 'boolean?' }, display: { zh: '按下键盘', en: 'Pressing key' } });

registerAction('dom.scroll', async ({ selector, top, left, deltaY, deltaX, intoView, block, inline }: { selector?: string; top?: number; left?: number; deltaY?: number; deltaX?: number; intoView?: boolean; block?: ScrollLogicalPosition; inline?: ScrollLogicalPosition }) => {
  const el = selector ? (qs(selector) as HTMLElement | null) : null;
  if (selector && !el) throw new Error('element not found: ' + selector);
  if (intoView && el) {
    el.scrollIntoView({ block: block || 'center', inline: inline || 'nearest' });
  } else if (el) {
    if (typeof top === 'number') el.scrollTop = top;
    if (typeof left === 'number') el.scrollLeft = left;
    if (typeof deltaY === 'number' || typeof deltaX === 'number') el.scrollBy({ top: Number(deltaY) || 0, left: Number(deltaX) || 0, behavior: 'auto' });
  } else {
    if (typeof top === 'number' || typeof left === 'number') window.scrollTo({ top: typeof top === 'number' ? top : window.scrollY, left: typeof left === 'number' ? left : window.scrollX, behavior: 'auto' });
    if (typeof deltaY === 'number' || typeof deltaX === 'number') window.scrollBy({ top: Number(deltaY) || 0, left: Number(deltaX) || 0, behavior: 'auto' });
  }
  return el
    ? { selector, scrollTop: el.scrollTop, scrollLeft: el.scrollLeft, rect: el.getBoundingClientRect().toJSON?.() || null }
    : { selector: null, scrollX: window.scrollX, scrollY: window.scrollY };
}, { description: 'Scroll window/container or scroll an element into view', args: { selector: 'string?', top: 'number?', left: 'number?', deltaY: 'number?', deltaX: 'number?', intoView: 'boolean?', block: 'string?', inline: 'string?' }, display: { zh: '滚动页面', en: 'Scrolling' } });

registerAction('dom.wait', async ({ selector, timeout }: { selector: string; timeout?: number }) => {
  const to = Math.min(Math.max(Number(timeout) || 5000, 100), 30000);
  const deadline = Date.now() + to;
  while (Date.now() < deadline) {
    if (document.querySelector(selector)) return { matched: selector };
    await sleep(100);
  }
  throw new Error('timeout waiting for ' + selector);
}, { description: 'Wait for the element to appear (default 5s)', args: { selector: 'string', timeout: 'number ms' }, display: { zh: '正在等待元素', en: 'Waiting for element' } });

registerAction('dom.waitVisible', async ({ selector, timeout }: { selector: string; timeout?: number }) => {
  const to = Math.min(Math.max(Number(timeout) || 5000, 100), 30000);
  const deadline = Date.now() + to;
  while (Date.now() < deadline) {
    const el = document.querySelector(selector);
    if (el && isVisible(el)) return { matched: selector, visible: true };
    await sleep(100);
  }
  const existsButHidden = !!document.querySelector(selector);
  throw new Error('timeout waiting for visible ' + selector + (existsButHidden ? ' (element exists but is not visible)' : ' (element not found)'));
}, { description: 'Wait until the element exists AND is visible. Default 5s.', args: { selector: 'string', timeout: 'number ms' }, display: { zh: '正在等待元素可见', en: 'Waiting for element visible' } });


registerAction('dom.waitGone', async ({ selector, timeout }: { selector: string; timeout?: number }) => {
  if (!selector) throw new Error('selector required');
  const to = Math.min(Math.max(Number(timeout) || 5000, 100), 30000);
  const deadline = Date.now() + to;
  while (Date.now() < deadline) {
    const el = document.querySelector(selector);
    if (!el || !isVisible(el)) return { gone: selector };
    await sleep(100);
  }
  throw new Error('timeout waiting for gone ' + selector);
}, { description: 'Wait until an element disappears or becomes invisible. Default 5s.', args: { selector: 'string', timeout: 'number ms' }, display: { zh: '正在等待元素消失', en: 'Waiting for element gone' } });

registerAction('dom.waitText', async ({ text, selector, exact, timeout }: { text: string; selector?: string; exact?: boolean; timeout?: number }) => {
  const needle = String(text || '').trim();
  if (!needle) throw new Error('text required');
  const scope = selector || 'body';
  const to = Math.min(Math.max(Number(timeout) || 5000, 100), 30000);
  const deadline = Date.now() + to;
  while (Date.now() < deadline) {
    const el = document.querySelector(scope);
    const hay = visibleText(el);
    if (exact ? hay === needle : hay.includes(needle)) return { matched: true, text: needle, selector: scope };
    await sleep(100);
  }
  throw new Error('timeout waiting for text ' + JSON.stringify(needle) + ' in ' + scope);
}, { description: 'Wait until visible text appears in a selector scope (default body). Default 5s.', args: { text: 'string', selector: 'string?', exact: 'boolean?', timeout: 'number ms' }, display: { zh: '正在等待文本出现', en: 'Waiting for text' } });

registerAction('dom.query', async ({ selector, limit }: { selector: string; limit?: number }) => {
  const cap = Math.min(Math.max(Number(limit) || 20, 1), 100);
  const all = Array.from(document.querySelectorAll(selector));
  const list = all.slice(0, cap);
  return { count: all.length, returned: list.length, items: list.map((el) => summarizeElement(el)) };
}, { description: 'Return summary list of matching elements', args: { selector: 'string', limit: 'int' }, display: { zh: '正在查找元素', en: 'Querying elements' } });

registerAction('dom.select', async ({ selector, value, label }: { selector: string; value?: string; label?: string }) => {
  const el = qs(selector) as HTMLSelectElement | null;
  if (!el) throw new Error('element not found: ' + selector);
  if (el.tagName.toLowerCase() !== 'select') throw new Error('dom.select target is not a <select>: ' + selector);
  const options = Array.from(el.options);
  let matched = value !== undefined && value !== null && value !== '' ? options.find((o) => o.value === String(value)) : undefined;
  if (!matched && label !== undefined && label !== null && label !== '') {
    const needle = String(label).trim();
    matched = options.find((o) => (o.textContent || '').trim() === needle) || options.find((o) => (o.textContent || '').trim().includes(needle));
  }
  if (!matched) throw new Error('no <option> matched value/label; available=' + JSON.stringify(options.map((o) => ({ value: o.value, label: (o.textContent || '').trim() }))));
  Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(el, matched.value);
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
  return { selected: matched.value, label: (matched.textContent || '').trim() };
}, { description: 'Set a <select> value by option value or visible label and dispatch input+change', args: { selector: 'string', value: 'string?', label: 'string?' }, display: { zh: '选择下拉项', en: 'Selecting option' } });

registerAction('dom.check', async ({ selector, checked }: { selector: string; checked?: boolean }) => {
  const el = qs(selector) as HTMLInputElement | null;
  if (!el) throw new Error('element not found: ' + selector);
  const type = (el.getAttribute('type') || '').toLowerCase();
  if (el.tagName.toLowerCase() !== 'input' || (type !== 'checkbox' && type !== 'radio')) throw new Error('dom.check target must be a checkbox/radio input: ' + selector);
  const target = checked === undefined ? !el.checked : !!checked;
  if (el.checked !== target) {
    el.scrollIntoView({ block: 'center', inline: 'center' });
    el.click();
  }
  if (el.checked !== target && type === 'checkbox') {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'checked')?.set?.call(el, target);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }
  return { selector, checked: el.checked };
}, { description: 'Toggle or set a checkbox/radio input; omit checked to toggle', args: { selector: 'string', checked: 'boolean?' }, display: { zh: '切换勾选状态', en: 'Toggling checkbox' } });

registerAction('dom.clickText', async ({ text, selector, exact }: { text: string; selector?: string; exact?: boolean }) => {
  const el = findByText(text, { selector, exact });
  if (!el) throw new Error('no visible element matched text: ' + text);
  el.scrollIntoView({ block: 'center', inline: 'center' });
  el.click();
  return { clicked_text: text, tag: el.tagName.toLowerCase(), testid: el.getAttribute('data-testid') || null };
}, { description: 'Click first visible element matching text. Fallback when no stable selector.', args: { text: 'string', selector: 'string?', exact: 'boolean?' }, display: { zh: '按文本点击', en: 'Clicking by text' } });

registerAction('nav.goto', async ({ path }: { path: string }) => {
  if (typeof path !== 'string') throw new Error('path required');
  if (path.startsWith('#')) location.hash = path;
  else if (path.startsWith('/')) {
    history.pushState({}, '', path);
    window.dispatchEvent(new PopStateEvent('popstate'));
  } else location.assign(path);
  return { navigated_to: path, current: location.pathname + location.hash };
}, { description: 'Client-side route navigation', args: { path: 'string' }, display: { zh: '跳转页面', en: 'Navigating' } });

registerAction('nav.refresh', async ({ reason }: { reason?: string } = {}) => {
  const detail = { reason: reason || 'page-control', at: Date.now() };
  window.dispatchEvent(new CustomEvent('aime:page-control-refresh', { detail }));
  window.dispatchEvent(new CustomEvent('pageControlRefresh', { detail }));
  window.dispatchEvent(new PopStateEvent('popstate'));
  return { refreshed: true, mode: 'soft', event: 'aime:page-control-refresh', current: location.pathname + location.hash };
}, { description: 'Soft-refresh page data without reloading the iframe or breaking WebSocket; apps can listen to aime:page-control-refresh or register custom refresh actions', args: { reason: 'string?' }, display: { zh: '刷新页面数据', en: 'Refreshing page data' } });

const state: PageControlState = { connected: false, transport: 'idle', sessionId: '', assistantId: '', username: '', lastError: '', actionCount: 0 };
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
const CONTROLLING_EVENT = 'pageControlControlling';
const CONTROLLING_IDLE_MS = 20000;
const CONTROL_END_DELAY_MS = 2500;
const FOCUS_HIGHLIGHT_MS = 1200;
let controllingIdleTimer: ReturnType<typeof setTimeout> | null = null;

function emitControlling(detail: { active: boolean; actionName?: string; display?: { zh?: string; en?: string } | null }) {
  window.dispatchEvent(new CustomEvent(CONTROLLING_EVENT, { detail }));
}

const SILENT_ACTIONS = new Set(['__describe__', '__control_start__', '__control_end__']);
let explicitControlActive = false;

function markControlStart(display: { zh?: string; en?: string } | null) {
  emitControlling({ active: true, actionName: '__control_start__', display });
  if (controllingIdleTimer) clearTimeout(controllingIdleTimer);
  controllingIdleTimer = null;
}

function markActionStart(name: string, meta: { display: { zh?: string; en?: string } | null }) {
  if (SILENT_ACTIONS.has(name)) return;
  markControlStart(meta.display);
}

function markActionEnd(name: string) {
  if (SILENT_ACTIONS.has(name)) return;
  if (explicitControlActive) return;
  if (controllingIdleTimer) clearTimeout(controllingIdleTimer);
  controllingIdleTimer = setTimeout(() => {
    controllingIdleTimer = null;
    emitControlling({ active: false });
  }, CONTROLLING_IDLE_MS);
}

function clearControllingAfterDelay() {
  if (controllingIdleTimer) clearTimeout(controllingIdleTimer);
  controllingIdleTimer = setTimeout(() => {
    controllingIdleTimer = null;
    emitControlling({ active: false });
  }, CONTROL_END_DELAY_MS);
}

const focusTimers = new WeakMap<Element, ReturnType<typeof setTimeout>>();
function highlightElement(el: Element | null) {
  if (!el) return;
  const he = el as HTMLElement;
  he.setAttribute('data-agent-focus', 'true');
  const prev = focusTimers.get(el);
  if (prev) clearTimeout(prev);
  const timer = setTimeout(() => {
    he.removeAttribute('data-agent-focus');
    focusTimers.delete(el);
  }, FOCUS_HIGHLIGHT_MS);
  focusTimers.set(el, timer);
}

function highlightForAction(name: string, args: any) {
  try {
    if (!args || typeof args !== 'object') return;
    if (typeof args.selector === 'string' && args.selector) return highlightElement(document.querySelector(args.selector));
    if (name === 'dom.clickText' && typeof args.text === 'string') highlightElement(findByText(args.text, { selector: args.selector, exact: args.exact }));
  } catch {
    // best effort only
  }
}

async function handleActionRequest(action: string, args?: any): Promise<any> {
  const entry = actions.get(action);
  if (!entry) return { ok: false, error: 'unknown action: ' + action };
  state.actionCount += 1;
  markActionStart(action, { display: entry.display });
  if (action.startsWith('dom.')) highlightForAction(action, args || {});
  try {
    const result = await entry.handler(args || {});
    return { ok: true, action, data: result };
  } catch (e: any) {
    return { ok: false, error: e?.message || String(e) };
  } finally {
    markActionEnd(action);
  }
}

async function handlePageControlRequest(msg: WSEnvelope): Promise<any> {
  if (msg.method === WS_METHOD_PAGE_DESCRIBE) return handleActionRequest('__describe__', {});
  if (msg.method === WS_METHOD_PAGE_STATE) return handleActionRequest('__state__', {});
  if (msg.method === WS_METHOD_PAGE_ACTION) {
    const payload = (msg.payload && typeof msg.payload === 'object' ? msg.payload : {}) as { action?: string; args?: any };
    if (!payload.action) return { ok: false, error: 'page.action payload.action required' };
    return handleActionRequest(payload.action, payload.args || {});
  }
  return { ok: false, error: 'unknown page-control method: ' + (msg.method || '') };
}

async function handleWSRequest(msg: WSEnvelope): Promise<any> {
  switch (msg.channel) {
    case WS_CHANNEL_PAGE_CONTROL:
      return handlePageControlRequest(msg);
    default:
      return { ok: false, error: 'unknown websocket channel: ' + (msg.channel || '') };
  }
}

function sendWSResponse(ws: WebSocket, req: WSEnvelope, result: any) {
  const ok = result?.ok !== false;
  const envelope: WSEnvelope = {
    type: 'response',
    id: req.id,
    channel: req.channel,
    method: req.method,
    ok,
    payload: result,
  };
  if (!ok) envelope.error = result?.error || 'websocket request failed';
  try { ws.send(JSON.stringify(envelope)); } catch (e) { warn('ws send response failed', e); }
}

let stopped = false;
function connectWebSocket(sessionId: string): Promise<WebSocket> {
  return new Promise(async (resolve, reject) => {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const jwt = await fetchJwt();
    const params = new URLSearchParams();
    params.set('session_id', sessionId);
    if (jwt) params.set('access_token', jwt);
    params.set('init_time', String(window.__pageControlInitTime__ || 0));
    const ws = new WebSocket(`${proto}//${location.host}/ws/page-control?${params.toString()}`);
    const timer = setTimeout(() => {
      try { ws.close(); } catch { /* noop */ }
      reject(new Error('websocket handshake timeout'));
    }, 3000);
    ws.onopen = () => { clearTimeout(timer); resolve(ws); };
    ws.onerror = () => { clearTimeout(timer); reject(new Error('websocket error')); };
    ws.onclose = () => { clearTimeout(timer); reject(new Error('websocket closed before open')); };
  });
}

async function runWebSocket(ws: WebSocket): Promise<void> {
  state.connected = true;
  state.transport = 'ws';
  const pingTimer = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      try { ws.send(JSON.stringify({ type: 'ping' })); } catch (e) { warn('ws ping failed', e); }
    }
  }, 25000);
  return new Promise((resolve) => {
    ws.onmessage = async (ev) => {
      let msg: any;
      try { msg = JSON.parse(String(ev.data)); } catch { return; }
      if (!msg || typeof msg !== 'object' || msg.type === 'pong' || msg.type === 'hello') return;
      if (msg.type === 'event') {
        if (msg.event === 'data-changed') {
          window.dispatchEvent(new CustomEvent('aime:data-changed', { detail: msg.payload || {} }));
          window.dispatchEvent(new CustomEvent('aime:page-control-refresh', { detail: { reason: 'data-changed', ...(msg.payload || {}) } }));
          window.dispatchEvent(new CustomEvent('pageControlRefresh', { detail: { reason: 'data-changed', ...(msg.payload || {}) } }));
        }
        return;
      }
      if (msg.type === 'request') {
        const result = await handleWSRequest(msg);
        sendWSResponse(ws, msg, result);
        return;
      }
    };
    ws.onclose = () => {
      clearInterval(pingTimer);
      state.connected = false;
      state.transport = 'idle';
      resolve();
    };
    ws.onerror = () => {
      state.lastError = 'websocket error';
    };
  });
}

async function bootstrap(): Promise<{ ok: boolean; reason?: string; sessionId?: string; assistantId?: string; username?: string }> {
  const env = detectEnv();
  if (!env.inIframe) return { ok: false, reason: 'not_in_iframe' };
  if (env.nested) return { ok: false, reason: 'nested_iframe_skip' };
  const cfg = await fetchAimeConfig();
  if (!cfg?.assistant_id || !cfg?.username) return { ok: false, reason: 'config_missing' };
  const sessionId = cfg.session_id || `${cfg.assistant_id}_${cfg.username}`;
  state.sessionId = sessionId;
  state.assistantId = cfg.assistant_id;
  state.username = cfg.username;
  return new Promise((resolve) => {
    let readyResolved = false;
    const resolveReady = (value: { ok: boolean; reason?: string; sessionId?: string; assistantId?: string; username?: string }) => {
      if (readyResolved) return;
      readyResolved = true;
      resolve(value);
    };
    void (async () => {
      while (!stopped) {
        try {
          const ws = await connectWebSocket(sessionId);
          state.lastError = '';
          resolveReady({ ok: true, sessionId, assistantId: cfg.assistant_id, username: cfg.username });
          await runWebSocket(ws);
        } catch (e: any) {
          state.connected = false;
          state.transport = 'idle';
          state.lastError = e?.message || String(e);
          warn('websocket unavailable', e);
        }
        if (!stopped) await sleep(1500);
      }
      resolveReady({ ok: false, reason: 'stopped', sessionId, assistantId: cfg.assistant_id, username: cfg.username });
    })();
  });
}

export function initPageControl() {
  if (window.__pageControlInit__) return;
  window.__pageControlInit__ = true;
  window.__pageControlInitTime__ = window.__pageControlInitTime__ || Date.now();
  const ready = bootstrap();
  const api: PageControlGlobal = {
    ready,
    status: () => ({ ...state, actions: actions.size, stateProviders: stateProviders.size }),
    registerAction,
    unregisterAction,
    listActions,
    registerStateProvider,
    unregisterStateProvider,
  };
  window.__pageControlLoaded__ = true;
  window.pageControl = api;
  log('initialized');
}

export function stopPageControl() {
  stopped = true;
}
