import type { ReactNode } from 'react';
import { Message, Notification } from '@arco-design/web-react';

export type AimeMessageType = 'success' | 'error' | 'info' | 'warning';

export interface AimeMessageOptions {
  type?: AimeMessageType;
  duration?: number;
  id?: string;
  closable?: boolean;
  onClose?: () => void;
}

// 与 Aime 宿主保持相同的堆叠上限；视觉由 Arco + Aime 主题桥接统一承载。
Message.config({
  maxCount: 3,
});
Notification.config({
  maxCount: 3,
});

/**
 * 展示短暂、单句、无需用户决策的操作反馈。
 *
 * 多行说明、持续状态或带操作的反馈应直接使用 Arco Notification；
 * 需要用户确认或输入时使用 Arco Modal / Form，而不是把 Message 当弹窗。
 */
export function showMessage(content: ReactNode, options: AimeMessageOptions = {}) {
  const {
    type = 'info',
    duration = 3000,
    ...messageOptions
  } = options;
  const config = { content, duration, ...messageOptions };

  switch (type) {
    case 'success':
      return Message.success(config);
    case 'error':
      return Message.error(config);
    case 'warning':
      return Message.warning(config);
    default:
      return Message.info(config);
  }
}
