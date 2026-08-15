import { useState, useEffect, createContext, useContext, ReactNode, useCallback } from 'react';
import { getCurrentUser, getJwtWithoutRedirect, redirectToLogin, redirectToUnauthorized, AuthError, AuthUser } from '../../auth';
import { useAimeText } from '../../aime-runtime';
import { Spin } from '@arco-design/web-react';

const authMessages = {
  zh: {
    loading: '正在验证登录状态...',
    forbiddenTitle: '无访问权限',
  },
  en: {
    loading: 'Verifying login status...',
    forbiddenTitle: 'Access Denied',
  },
};

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  authenticated: boolean;
  jwt: string | null;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  loading: true,
  authenticated: false,
  jwt: null,
});

export function useAuth() {
  return useContext(AuthContext);
}

/**
 * React 组件专用的 Fetch Hook，直接从 Context 获取 JWT，无任何异步开销。
 */
export function useApiFetch() {
  const { jwt } = useAuth();
  
  return useCallback(async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const headers = new Headers(init?.headers);
    if (jwt) {
      headers.set('Authorization', `Byte-Cloud-JWT ${jwt}`);
    }

    const response = await fetch(input, { ...init, headers });

    if (response.status === 401 || response.status === 403) {
      const url = typeof input === 'string' ? input : (input instanceof URL ? input.toString() : input.url);
      if (!url.includes('/api/me')) {
        redirectToUnauthorized(response.status);
      }
    }

    return response;
  }, [jwt]);
}

export function AuthGuard({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [jwt, setJwt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [forbiddenMessage, setForbiddenMessage] = useState('');
  const t = useAimeText(authMessages);

  useEffect(() => {
    let cancelled = false;

    async function checkAuth() {
      try {
        const u = await getCurrentUser();
        if (cancelled) return;

        const token = await getJwtWithoutRedirect();

        if (!u) {
          // 未登录，跳转 SSO
          await redirectToLogin();
          return;
        }

        setForbiddenMessage('');
        setUser(u);
        setJwt(token || null);
      } catch (e) {
        if (cancelled) return;
        console.error('[AuthGuard] 认证检查失败:', e);
        if (e instanceof AuthError && (e.status === 401 || e.status === 403)) {
          setUser(null);
          setForbiddenMessage(e.message || '当前账号无访问权限');
          redirectToUnauthorized(e.status);
          return;
        }
        await redirectToLogin();
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    checkAuth();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--aime-color-bg-base-default-1)' }}>
        <div style={{ textAlign: 'center' }}>
          <Spin dot size={20} />
          <p style={{ marginTop: 16, color: 'var(--aime-color-text-base-2)', fontSize: 14 }}>{t.loading}</p>
        </div>
      </div>
    );
  }

  if (forbiddenMessage) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', padding: 24, background: 'var(--aime-color-bg-base-default-1)' }}>
        <div style={{ maxWidth: 480, textAlign: 'center' }}>
          <h2 style={{ marginBottom: 12, fontSize: 20, color: 'var(--aime-color-text-base-highlight)' }}>{t.forbiddenTitle}</h2>
          <p style={{ color: 'var(--aime-color-text-base-2)', fontSize: 14, lineHeight: 1.6 }}>
            {forbiddenMessage}
          </p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, jwt, loading: false, authenticated: true }}>
      {children}
    </AuthContext.Provider>
  );
}
