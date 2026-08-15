import { Space, Typography } from '@arco-design/web-react';
import { useAimeText } from '../../aime-runtime';

const homeMessages = {
  zh: {
    title: '应用已就绪',
    description: '这是创建前端时生成的默认入口。开始实现业务前，先在路由规划中确认用户任务、主操作和页面状态。',
    next: '完成后可将此页面替换为实际工作台，或在 app-routes.tsx 登记新的业务路由。',
  },
  en: {
    title: 'Your app is ready',
    description: 'This is the default entry generated with a frontend. Plan the user task, primary action, and page states before implementing business views.',
    next: 'Replace this page with the real workspace or register new business routes in app-routes.tsx when ready.',
  },
};

export default function DefaultHomePage() {
  const t = useAimeText(homeMessages);

  return (
    <main style={{ minHeight: '100vh', padding: 'var(--aime-space-6)', background: 'var(--aime-color-bg-base-default-1)' }}>
      <Space direction="vertical" size="medium" style={{ width: '100%', maxWidth: 680 }}>
        <Typography.Title heading={5} style={{ margin: 0 }}>{t.title}</Typography.Title>
        <Typography.Paragraph style={{ margin: 0, lineHeight: 1.7 }}>{t.description}</Typography.Paragraph>
        <Typography.Text type="secondary">{t.next}</Typography.Text>
      </Space>
    </main>
  );
}
