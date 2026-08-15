import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { AskPage, LibraryPage, PaperPage, ReportPage, ReportsPage, SettingsPage } from './pages/workspace';

export interface AppRouteDefinition {
  path: `/${string}`;
  element: ReactNode;
}

export const BUSINESS_ROUTES: AppRouteDefinition[] = [
  { path: '/library', element: <LibraryPage /> },
  { path: '/papers/:paperId', element: <PaperPage /> },
  { path: '/ask', element: <AskPage /> },
  { path: '/reports', element: <ReportsPage /> },
  { path: '/reports/:reportId', element: <ReportPage /> },
  { path: '/settings', element: <SettingsPage /> },
  { path: '/', element: <Navigate to="/library" replace /> },
];
