// CODE GENERATED FROM app/api/api.yaml BY tools/gen_api.py — DO NOT EDIT
import { apiFetch } from '../auth';

export type ApiEnvelope<T = unknown> = { data: T } & Record<string, unknown>;
export function unwrap<T>(res: { data: T }): T { return res.data; }

export interface ItemsModel {
  id: string;
  title: string;
  description: string;
  status: string;
  createdAt: string;
  updatedAt: string;
}

export type ItemsListResponse = { data: ItemsModel[]; total: number; backend: string };
export type ItemsCreateResponse = { data: { id: string; title: string; status: string }; backend: string };
export type ItemsByIdDeleteResponse = { success: boolean; backend: string };
export type ItemsByIdGetResponse = { data: { id: string; title: string; status: string }; backend: string };
export type ItemsByIdUpdateResponse = { data: { id: string; title: string; status: string }; backend: string };

async function request<T>(method: string, path: string, body?: unknown, query?: Record<string, unknown>): Promise<T> {
  let url = path;
  if (query) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined && v !== null) qs.append(k, String(v));
    }
    const s = qs.toString();
    if (s) url += `?${s}`;
  }
  const res = await apiFetch(url, {
    method,
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });
  if (!res.ok) throw new Error(`${method} ${path} failed: HTTP ${res.status}`);
  const text = await res.text();
  return (text ? JSON.parse(text) : {}) as T;
}

/** GET /api/items — 列出所有项目 */
export function itemsList<T = ItemsListResponse>(): Promise<T> {
  return request<T>("GET", '/api/items', undefined);
}

/** POST /api/items — 创建项目 */
export function itemsCreate<T = ItemsCreateResponse>(body: {
  title: string; /** 项目标题，不能为空 */
  description?: string; /** 项目描述，可选 */
  status?: string; /** 项目状态，例如 todo/done */
}): Promise<T> {
  return request<T>("POST", '/api/items', body);
}

/** DELETE /api/items/{id} — 删除项目 */
export function itemsByIdDelete<T = ItemsByIdDeleteResponse>(id: string | number): Promise<T> {
  return request<T>("DELETE", `/api/items/${id}`, undefined);
}

/** GET /api/items/{id} — 获取单个项目 */
export function itemsByIdGet<T = ItemsByIdGetResponse>(id: string | number): Promise<T> {
  return request<T>("GET", `/api/items/${id}`, undefined);
}

/** PUT /api/items/{id} — 更新项目（字段可选） */
export function itemsByIdUpdate<T = ItemsByIdUpdateResponse>(id: string | number, body: {
  title?: string; /** 新项目标题，可选 */
  description?: string; /** 新项目描述，可选 */
  status?: string; /** 新项目状态，可选，例如 todo/done */
}): Promise<T> {
  return request<T>("PUT", `/api/items/${id}`, body);
}
