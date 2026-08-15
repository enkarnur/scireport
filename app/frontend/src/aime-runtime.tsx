import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { useAime } from '@aime-plugin/browser-sdk/dynamic-ui/react';

type SupportedLocale = 'zh' | 'en';
type LocaleMessages<T extends Record<string, string>> = Record<SupportedLocale, T>;

export const runtimeExampleMessages = {
  zh: {
    title: '前端运行时接入检查',
    description: '此占位页仅验证主题、语言和会话上下文。开发时请用真实业务入口替换。',
    themeLabel: '主题',
    localeLabel: '语言',
    sessionLabel: '会话',
  },
  en: {
    title: 'Frontend runtime check',
    description: 'This placeholder only verifies theme, locale, and session context. Replace it with the real product entry.',
    themeLabel: 'Theme',
    localeLabel: 'Locale',
    sessionLabel: 'Session',
  },
} satisfies LocaleMessages<Record<string, string>>;

function normalizeLocale(locale: string): SupportedLocale {
  if (!locale) return 'zh';
  return locale.toLowerCase().startsWith('zh') ? 'zh' : 'en';
}

function getBrowserLocale(): SupportedLocale {
  if (typeof navigator !== 'undefined' && navigator.language) {
    return navigator.language.toLowerCase().startsWith('zh') ? 'zh' : 'en';
  }
  return 'zh';
}

function isInAimeHost(): boolean {
  return typeof window !== 'undefined' && !!(window as any).__aime__;
}

export function useAimeText<T extends Record<string, string>>(messages: LocaleMessages<T>): T {
  const { locale } = useAime();
  const resolved = isInAimeHost() ? normalizeLocale(locale) : getBrowserLocale();
  return messages[resolved];
}

export interface PageControlRefreshDetail {
  reason?: string;
  at?: number;
}

/**
 * 监听 page-control 的不断链软刷新事件。
 *
 * Agent/CLI 在后端 api call 写入数据后通常会执行：
 *   page action nav.refresh
 * nav.refresh 不会重载 iframe，也不会自动知道业务组件如何重新拉数据；
 * 它只派发刷新事件。数据页应使用本 hook，在事件到来时调用自己的 load()/bump()。
 */
export function usePageControlRefresh(callback: (detail: PageControlRefreshDetail) => void): void {
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = event instanceof CustomEvent && event.detail && typeof event.detail === 'object'
        ? event.detail as PageControlRefreshDetail
        : {};
      callbackRef.current(detail);
    };
    window.addEventListener('aime:page-control-refresh', handler);
    window.addEventListener('pageControlRefresh', handler);
    return () => {
      window.removeEventListener('aime:page-control-refresh', handler);
      window.removeEventListener('pageControlRefresh', handler);
    };
  }, []);
}

export interface DataChangedDetail {
  resource?: string;
  at?: number;
}

/**
 * 监听后端数据变更事件。
 *
 * 当集成层（CLI/Command/Hook/Skill）写操作成功后自动调用 notify_refresh() 时，
 * 后端通过 WebSocket 推送 data-changed 事件，本 hook 的 callback 会被触发。
 * 业务页在 callback 中重新拉取数据即可实现自动刷新。
 *
 * 推荐直接使用 useApiData()，已内置 data-changed + nav.refresh 监听。
 */
export function useDataRefresh(callback: (detail: DataChangedDetail) => void): void {
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = event instanceof CustomEvent && event.detail && typeof event.detail === 'object'
        ? event.detail as DataChangedDetail
        : {};
      callbackRef.current(detail);
    };
    window.addEventListener('aime:data-changed', handler);
    return () => {
      window.removeEventListener('aime:data-changed', handler);
    };
  }, []);
}

export function useApiData<T>(
  fetcher: () => Promise<T>,
  resource?: string
): { data: T | null; loading: boolean; reload: () => void } {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const fetcherRef = useRef(fetcher);

  useEffect(() => {
    fetcherRef.current = fetcher;
  }, [fetcher]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await fetcherRef.current());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  useDataRefresh((detail) => {
    if (!resource || !detail.resource || detail.resource === resource) {
      void load();
    }
  });

  usePageControlRefresh(() => { void load(); });

  return { data, loading, reload: load };
}

export function AimeRuntimeEffects({ children }: { children: ReactNode }) {
  const { runtime, locale } = useAime();

  useEffect(() => {
    if (!runtime) {
      return;
    }

    const theme = runtime.theme || 'light';
    document.documentElement.lang = isInAimeHost() ? normalizeLocale(locale || runtime.locale) : getBrowserLocale();
    document.body.setAttribute('data-theme', theme);
    document.body.setAttribute('theme-mode', theme);
    document.body.setAttribute('arco-theme', theme);
  }, [locale, runtime]);

  return <>{children}</>;
}
