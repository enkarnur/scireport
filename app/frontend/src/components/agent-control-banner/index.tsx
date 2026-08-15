import { useEffect, useRef, useState } from 'react';
import { useAimeText } from '../../aime-runtime';

// -------- 事件契约 --------
// page-control-runtime.ts 在收到 action 时 dispatch 一次 { active: true, actionName, display }，
// 在最后一条 action 结束 20s 无新 action 后 dispatch { active: false }。
// 顶部条是 session 级：中间连续 action 只 fade 文案，条本身不 slide 出去。
interface ControllingEventDetail {
  active: boolean;
  actionName?: string;
  display?: { zh?: string; en?: string } | null;
}

// -------- i18n --------
const bannerMessages = {
  zh: {
    prefix: '✦ Aime 正在控制中',
    fallbackAction: '正在操作…',
  },
  en: {
    prefix: '✦ Aime is controlling',
    fallbackAction: 'Operating...',
  },
};

// 短文案淡入淡出过渡的时长；实际把文案 apply 到 DOM 前会保留旧文案，等淡出完再切换。
const TEXT_FADE_MS = 160;
// slide-in / fade-out 与 CSS 里保持一致
const SLIDE_MS = 260;

type Phase = 'idle' | 'entering' | 'visible' | 'leaving';

function pickDisplay(locale: 'zh' | 'en', display?: { zh?: string; en?: string } | null): string {
  if (!display) return '';
  return (locale === 'zh' ? display.zh : display.en) || display.zh || display.en || '';
}

/**
 * 「Aime 正在控制中」顶部状态条。
 *
 * 生命周期（session 级）：
 *   idle ──(active=true)──▶ entering ──(SLIDE_MS)──▶ visible
 *     ▲                                                 │
 *     │                                    (active=false)│
 *     │                                                 ▼
 *     └────────────(SLIDE_MS)──────── leaving ◀─────────┘
 *
 * 中间连续 action：只 fade 内文；条本身不 slide 出去。
 * 条自身不拦截交互 (`pointer-events: none`)，Tab 点击等在下面照常工作。
 */
export function AgentControlBanner() {
  const t = useAimeText(bannerMessages);

  const [phase, setPhase] = useState<Phase>('idle');
  const [renderedText, setRenderedText] = useState<string>('');
  const [textFadeIn, setTextFadeIn] = useState<boolean>(true);

  // 保存最近一次 display 以便切 locale 时能重新计算文案
  const lastDisplayRef = useRef<{ zh?: string; en?: string } | null>(null);
  const phaseRef = useRef<Phase>('idle');
  const renderedTextRef = useRef<string>('');
  const enterTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const leaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const textTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 通过 t.prefix 反查当前 locale（避免额外依赖 useAime）
  const localeGuess: 'zh' | 'en' = t.prefix.includes('Aime 正') ? 'zh' : 'en';

  // 保持 refs 与 state 同步
  useEffect(() => {
    phaseRef.current = phase;
  }, [phase]);
  useEffect(() => {
    renderedTextRef.current = renderedText;
  }, [renderedText]);

  useEffect(() => {
    const clearEnter = () => {
      if (enterTimerRef.current) {
        clearTimeout(enterTimerRef.current);
        enterTimerRef.current = null;
      }
    };
    const clearLeave = () => {
      if (leaveTimerRef.current) {
        clearTimeout(leaveTimerRef.current);
        leaveTimerRef.current = null;
      }
    };
    const clearText = () => {
      if (textTimerRef.current) {
        clearTimeout(textTimerRef.current);
        textTimerRef.current = null;
      }
    };

    const goEntering = (nextText: string) => {
      clearLeave();
      clearEnter();
      setRenderedText(nextText);
      setTextFadeIn(true);
      setPhase('entering');
      phaseRef.current = 'entering';
      enterTimerRef.current = setTimeout(() => {
        setPhase('visible');
        phaseRef.current = 'visible';
      }, SLIDE_MS);
    };

    const fadeTextTo = (nextText: string) => {
      if (renderedTextRef.current === nextText) return;
      clearText();
      setTextFadeIn(false);
      textTimerRef.current = setTimeout(() => {
        setRenderedText(nextText);
        setTextFadeIn(true);
      }, TEXT_FADE_MS);
    };

    const onControlling = (ev: Event) => {
      const detail = (ev as CustomEvent<ControllingEventDetail>).detail;
      if (!detail) return;

      if (detail.active) {
        lastDisplayRef.current = detail.display ?? null;
        const nextText = pickDisplay(localeGuess, detail.display) || t.fallbackAction;
        const cur = phaseRef.current;

        if (cur === 'idle' || cur === 'leaving') {
          // slide-in
          goEntering(nextText);
        } else {
          // entering / visible：只 fade 文案，条本身不动
          fadeTextTo(nextText);
        }
      } else {
        const cur = phaseRef.current;
        if (cur === 'idle') return;
        // 进入 leaving，SLIDE_MS 后回到 idle
        clearLeave();
        setPhase('leaving');
        phaseRef.current = 'leaving';
        leaveTimerRef.current = setTimeout(() => {
          setPhase('idle');
          phaseRef.current = 'idle';
        }, SLIDE_MS);
      }
    };

    window.addEventListener('pageControlControlling', onControlling as EventListener);
    return () => {
      window.removeEventListener('pageControlControlling', onControlling as EventListener);
      clearEnter();
      clearLeave();
      clearText();
    };
  }, [localeGuess, t.fallbackAction]);

  // locale 切换时回填当前文案
  useEffect(() => {
    if (phaseRef.current === 'idle') return;
    const nextText = pickDisplay(localeGuess, lastDisplayRef.current) || t.fallbackAction;
    setRenderedText(nextText);
    setTextFadeIn(true);
  }, [localeGuess, t.fallbackAction]);

  if (phase === 'idle') return null;

  const visible = phase === 'entering' || phase === 'visible';

  return (
    <div
      className={`agent-control-banner ${
        visible ? 'agent-control-banner--visible' : 'agent-control-banner--leaving'
      }`}
      role="status"
      aria-live="polite"
    >
      <div className="agent-control-banner__inner">
        <span className="agent-control-banner__prefix">{t.prefix}</span>
        <span
          className={`agent-control-banner__text ${
            textFadeIn ? 'agent-control-banner__text--in' : 'agent-control-banner__text--out'
          }`}
        >
          {renderedText || t.fallbackAction}
        </span>
      </div>
    </div>
  );
}

export default AgentControlBanner;
