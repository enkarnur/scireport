import type { ReactNode } from 'react';
import { BrowserRouter, Navigate, Routes, Route } from 'react-router-dom';
import { AimeProvider } from '@aime-plugin/browser-sdk/dynamic-ui/react';
import { AimeRuntimeEffects } from './aime-runtime';
import { BUSINESS_ROUTES } from './app-routes';
import { AuthGuard } from './components/auth-guard';
import AgentControlBanner from './components/agent-control-banner';
import UnauthorizedPage from './pages/unauthorized';

function GuardedRoute({ children }: { children: ReactNode }) {
  return <AuthGuard>{children}</AuthGuard>;
}

export default function App() {
  return (
    <AimeProvider>
      <AimeRuntimeEffects>
        <BrowserRouter>
          <Routes>
            <Route path="/unauthorized" element={<UnauthorizedPage />} />
            {BUSINESS_ROUTES.map(({ path, element }) => (
              <Route
                key={path}
                path={path}
                element={<GuardedRoute>{element}</GuardedRoute>}
              />
            ))}
            {/* 参考页源码不进入生产 Router；首条业务路由同时作为安全回退。 */}
            <Route path="*" element={<Navigate to={BUSINESS_ROUTES[0]?.path || '/unauthorized'} replace />} />
          </Routes>
          {/* 顶部「Aime 正在控制中」状态条，由 page-control runtime 事件驱动 */}
          <AgentControlBanner />
        </BrowserRouter>
      </AimeRuntimeEffects>
    </AimeProvider>
  );
}
