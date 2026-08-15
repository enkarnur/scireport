(function initAimeElementPicker() {
  if (window.self === window.top) return;

  function getAimeAttributes(el: Element): {
    filePath?: string;
    line?: number;
    column?: number;
    componentName?: string;
  } | null {
    let current: Element | null = el;
    while (current) {
      const pathName = current.getAttribute('data-aime-path-name');
      if (pathName) {
        return {
          filePath: pathName,
          line: parseInt(current.getAttribute('data-aime-line') || '0', 10) || undefined,
          column: parseInt(current.getAttribute('data-aime-column') || '0', 10) || undefined,
          componentName: current.getAttribute('data-aime-component-name') || undefined,
        };
      }
      current = current.parentElement;
    }
    return null;
  }

  function getReactFiberInfo(el: Element): {
    componentName?: string;
    filePath?: string;
    line?: number;
    column?: number;
  } | null {
    const fiberKey = Object.keys(el).find((k) => k.startsWith('__reactFiber$'));
    if (!fiberKey) return null;
    let fiber = (el as any)[fiberKey];
    while (fiber) {
      if (fiber._debugSource) {
        const source = fiber._debugSource;
        const name = fiber.type?.displayName || fiber.type?.name || '';
        return {
          componentName: name || undefined,
          filePath: source.fileName || undefined,
          line: source.lineNumber || undefined,
          column: source.columnNumber || undefined,
        };
      }
      if (typeof fiber.type === 'function' || typeof fiber.type === 'object') {
        const name = fiber.type?.displayName || fiber.type?.name;
        if (name) {
          return { componentName: name };
        }
      }
      fiber = fiber.return;
    }
    return null;
  }

  function queryElement(x: number, y: number) {
    const el = document.elementFromPoint(x, y);
    if (!el) {
      window.parent.postMessage({ type: '__aime_pick_result', data: null }, '*');
      return;
    }
    const rect = el.getBoundingClientRect();
    const attrs = getAimeAttributes(el);
    const fiberInfo = !attrs ? getReactFiberInfo(el) : null;
    const info = attrs || fiberInfo;

    window.parent.postMessage(
      {
        type: '__aime_pick_result',
        data: {
          rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
          tagName: el.tagName.toLowerCase(),
          componentName: info?.componentName || undefined,
          filePath: info?.filePath || undefined,
          line: info?.line || undefined,
          column: info?.column || undefined,
        },
      },
      '*',
    );
  }

  window.addEventListener('message', (event) => {
    const msg = event.data;
    if (!msg || typeof msg.type !== 'string') return;

    if (msg.type === '__aime_pick_query') {
      queryElement(msg.x, msg.y);
    }
  });

  window.parent.postMessage({ type: '__aime_picker_ready' }, '*');
})();
