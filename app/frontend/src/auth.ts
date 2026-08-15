// 认证工具模块 - 使用 @bytecloud/common-lib 获取字节云 JWT

export interface AuthUser {
  username: string;
  email?: string;
  avatar_url?: string;
  user_id?: string;
  org?: string;
  [key: string]: any;
}

export class AuthError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'AuthError';
    this.status = status;
  }
}

export const UNAUTHORIZED_ROUTE = '/unauthorized';

type DomainID = 'online' | 'boe' | 'sandbox' | 'i18n';

// 动态 import 避免模块加载时的副作用报错，并使用单例缓存
let jwtServicePromise: Promise<any> | null = null;
async function getJwtService() {
  if (!jwtServicePromise) {
    jwtServicePromise = import('@bytecloud/common-lib').then(m => m.bytecloudAsyncJwtService);
  }
  return jwtServicePromise;
}

function getDomainID(): DomainID {
  if (typeof window === 'undefined') return 'online';
  const host = window.location.host;
  if (host.includes('-boe')) return 'boe';
  return 'online';
}

export function redirectToUnauthorized(status?: number): void {
  if (typeof window === 'undefined') return;
  const params = new URLSearchParams();
  if (status !== undefined) params.set('status', String(status));
  
  // 保存当前路径，以便获得权限后能返回
  if (window.location.pathname !== UNAUTHORIZED_ROUTE) {
    params.set('redirect', window.location.pathname + window.location.search);
  }
  
  const query = params.toString();
  const target = query ? `${UNAUTHORIZED_ROUTE}?${query}` : UNAUTHORIZED_ROUTE;
  
  // 如果已经在未授权页且参数相同，则不重复跳转
  if (window.location.pathname + window.location.search === target) return;
  window.location.assign(target);
}

/**
 * 获取 JWT（会自动跳转 SSO 登录）
 */
export async function getJwt(): Promise<string> {
  if (typeof window === 'undefined') return '';
  const domainID = getDomainID();
  const service = await getJwtService();
  return service.getJwt(domainID);
}

/**
 * 尝试获取 JWT，未登录时不跳转
 */
export async function getJwtWithoutRedirect(): Promise<string | undefined> {
  if (typeof window === 'undefined') return undefined;
  try {
    const domainID = getDomainID();
    const service = await getJwtService();
    const jwtService = await service.getService(domainID);
    
    // _getLoginInfo 内部：先查 getCachedJwt（带 exp/region 校验，提前 5min 过期）→ miss 才 pureFetchJwt
    // → 成功后自动 setCache（写 localStorage['CLOUD_JWT_MAP']）+ saveJwt（写内存），401 静默返回不跳转。
    const info = await jwtService._getLoginInfo();
    if (info?.status === 200 && info.jwt) return info.jwt;
    return undefined;
  } catch (e) {
    console.warn('[auth] getJwtWithoutRedirect failed:', e);
    return undefined;
  }
}

/**
 * 跳转到登录页面
 */
export async function redirectToLogin(): Promise<void> {
  if (typeof window === 'undefined') return;
  const domainID = getDomainID();
  const service = await getJwtService();
  const jwtService = await service.getService(domainID);
  jwtService.redirectToLogin();
}

/**
 * 预热鉴权链路：应用启动时提前触发 @bytecloud/common-lib 的动态 import 与 JWT 获取，
 * 让那个鉴权 chunk 的下载/解析与 React 启动、首屏渲染并行，避免它被串进 AuthGuard
 * 首次校验的关键路径（getCurrentUser → 动态 import common-lib → /api/me 的串行瀑布）。
 * 使用不跳转版本以避免未登录时的副作用，失败静默（首个真实请求会再次按需触发）。
 */
let _jwtPrefetched = false;
export function prefetchJwt(): void {
  if (typeof window === 'undefined' || _jwtPrefetched) return;
  _jwtPrefetched = true;
  void getJwtWithoutRedirect().catch(() => {
    /* 预热失败忽略 */
  });
}

/**
 * 获取当前用户信息：先获取 JWT，然后通过后端 /api/me 查用户。
 * 无 JWT 时返回 null（由 AuthGuard 跳转登录）。
 */
export async function getCurrentUser(): Promise<AuthUser | null> {
  const jwt = await getJwtWithoutRedirect();
  if (!jwt) return null;

  const res = await fetch('/api/me', {
    headers: { Authorization: `Byte-Cloud-JWT ${jwt}` },
  });

  if (!res.ok) {
    let message = 'Auth request failed';
    try {
      const data = await res.json();
      message = data.error || data.message || message;
    } catch {
      // Ignore parse failures and keep the fallback message.
    }
    throw new AuthError(message, res.status);
  }

  const data = await res.json();
  return data.user || null;
}

/**
 * 带有鉴权头的 Fetch 封装。
 * 应用内请求后端 /api 接口请务必使用此方法，否则会返回 401/403。
 *
 * 401 处理：JWT 过期 → 静默刷新 → 成功则重试请求 → 失败则跳转 SSO 登录。
 * 403 处理：有身份但无权限 → 跳转无权限提示页。
 */
export async function apiFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const jwt = await getJwtWithoutRedirect();
  const headers = new Headers(init?.headers);
  if (jwt) {
    headers.set('Authorization', `Byte-Cloud-JWT ${jwt}`);
  }

  const response = await fetch(input, {
    ...init,
    headers,
  });

  if (response.status === 401) {
    const newJwt = await getJwtWithoutRedirect();
    if (newJwt && newJwt !== jwt) {
      const retryHeaders = new Headers(init?.headers);
      retryHeaders.set('Authorization', `Byte-Cloud-JWT ${newJwt}`);
      return fetch(input, { ...init, headers: retryHeaders });
    }
    await redirectToLogin();
    return response;
  }

  if (response.status === 403) {
    const url = typeof input === 'string' ? input : (input instanceof URL ? input.toString() : input.url);
    if (!url.includes('/api/me')) {
      redirectToUnauthorized(response.status);
    }
  }

  return response;
}
