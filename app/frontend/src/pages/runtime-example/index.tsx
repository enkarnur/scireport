import { useAime } from '@aime-plugin/browser-sdk/dynamic-ui/react';
import { runtimeExampleMessages, useAimeText } from '../../aime-runtime';

/**
 * Runtime 接入自检页：只演示 theme / locale / sessionId 与 useAimeText 的技术接法。
 * 创建真实应用时请用业务入口替换此路由，不要复用这里的内容或页面结构。
 */
export default function RuntimeExample() {
  const { theme, locale, sessionId } = useAime();
  const t = useAimeText(runtimeExampleMessages);

  return (
    <main
      className="p-4 text-sm"
      style={{
        color: 'var(--aime-color-text-base-1)',
        background: 'var(--aime-color-bg-base-default-1)',
      }}
    >
      <p className="m-0 font-medium">{t.title}</p>
      <p className="mt-2 mb-3" style={{ color: 'var(--aime-color-text-base-2)' }}>
        {t.description}
      </p>
      <dl className="m-0 text-xs" style={{ color: 'var(--aime-color-text-base-3)' }}>
        <dt className="inline">{t.themeLabel}: </dt><dd className="inline mr-3">{theme || '-'}</dd>
        <dt className="inline">{t.localeLabel}: </dt><dd className="inline mr-3">{locale || '-'}</dd>
        <dt className="inline">{t.sessionLabel}: </dt><dd className="inline">{sessionId ? sessionId.slice(0, 8) : '-'}</dd>
      </dl>
    </main>
  );
}
