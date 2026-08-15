import { useSearchParams, useNavigate } from 'react-router-dom';
import { Button } from '@arco-design/web-react';
import { useAimeText } from '../../aime-runtime';

const unauthorizedMessages = {
  zh: {
    title: '无访问权限',
    description: '当前账号没有访问权限，请联系应用管理员确认实例成员权限。',
    retry: '重新检测权限',
  },
  en: {
    title: 'No Access',
    description: 'Your account does not have access. Contact the app administrator to confirm instance membership.',
    retry: 'Check Again',
  },
};

export default function UnauthorizedPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const status = searchParams.get('status');
  const redirect = searchParams.get('redirect') || '/';
  const t = useAimeText(unauthorizedMessages);

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', padding: 24, background: 'var(--aime-color-bg-base-default-1)' }}>
      <div style={{ maxWidth: 520, textAlign: 'center' }}>
        <h1 style={{ marginBottom: 12, fontSize: 24, color: 'var(--aime-color-text-base-highlight)' }}>{t.title}</h1>
        <p style={{ marginBottom: 8, color: 'var(--aime-color-text-base-2)', fontSize: 14, lineHeight: 1.7 }}>
          {t.description}
        </p>
        {status ? (
          <p style={{ marginBottom: 24, color: 'var(--aime-color-text-base-3)', fontSize: 12 }}>
            HTTP Status: {status}
          </p>
        ) : null}
        <div style={{ marginTop: 24 }}>
          <Button type="primary" data-testid="unauthorized-retry-button" onClick={() => navigate(redirect, { replace: true })}>
            {t.retry}
          </Button>
        </div>
      </div>
    </div>
  );
}
