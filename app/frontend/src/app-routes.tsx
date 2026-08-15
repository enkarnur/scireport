import type { ReactNode } from 'react';
import DefaultHomePage from './pages/home';

export interface AppRouteDefinition {
  path: `/${string}`;
  element: ReactNode;
}

/**
 * 先按 information-architecture.md 完成路由规划表，再在这里登记真实业务路由。
 * 路由规划表属于设计与验收产物；本注册表只保留 React Router 实际消费的字段。
 * 小 App 可以共用源码文件，但每个稳定任务仍使用独立页面组件和 path。
 */
export const BUSINESS_ROUTES: AppRouteDefinition[] = [
  { path: '/', element: <DefaultHomePage /> },
];
