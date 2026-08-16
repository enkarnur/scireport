// CODE GENERATED FROM app/api/api.yaml BY tools/gen_api.py — DO NOT EDIT
import { apiFetch } from '../auth';

export type ApiEnvelope<T = unknown> = { data: T } & Record<string, unknown>;
export function unwrap<T>(res: { data: T }): T { return res.data; }

export interface AnnotationsModel {
  id: string;
  paperId: string;
  content: string;
  pageNumber: number;
  section: string;
  quote: string;
  startOffset: number;
  endOffset: number;
  color: string;
  createdAt: string;
  updatedAt: string;
}

export interface PapersModel {
  id: string;
  title: string;
  authors: unknown[];
  year: number;
  venue: string;
  doi: string;
  abstract: string;
  background: string;
  methods: string;
  results: string;
  discussion: string;
  processingStatus: string;
  pageCount: number;
  sourceFileName: string;
  createdAt: string;
  updatedAt: string;
}

export interface QaModel {
  id: string;
  question: string;
  answer: string;
  paperIds: unknown[];
  createdAt: string;
}

export interface ReportsModel {
  id: string;
  title: string;
  template: string;
  status: string;
  paperIds: unknown[];
  createdAt: string;
  updatedAt: string;
}

export interface SettingsModel {
  id: string;
  provider: string;
  baseUrl: string;
  model: string;
  hasApiKey: boolean;
  updatedAt: string;
}

export type AnnotationsListResponse = { data: Array<{ id: string; paperId: string; paperTitle: string; content: string; pageNumber: number; section: string; quote: string; startOffset: number; endOffset: number; color: string; createdAt: string; updatedAt: string }>; total: number; limit: number; offset: number };
export type AnnotationsCreateResponse = { data: { id: string; paperId: string; content: string; pageNumber: number; section: string; quote: string; startOffset: number; endOffset: number; color: string; createdAt: string; updatedAt: string } };
export type AnnotationsByAnnotationIdDeleteResponse = { success: boolean; deletedAnnotationId: string };
export type AnnotationsByAnnotationIdGetResponse = { data: { id: string; paperId: string; paperTitle: string; content: string; pageNumber: number; section: string; quote: string; startOffset: number; endOffset: number; color: string; createdAt: string; updatedAt: string } };
export type AnnotationsByAnnotationIdUpdateResponse = { data: { id: string; paperId: string; content: string; pageNumber: number; section: string; quote: string; startOffset: number; endOffset: number; color: string; createdAt: string; updatedAt: string } };
export type PapersListResponse = { data: Array<{ id: string; title: string; authors: Array<string>; year: number; venue: string; doi: string; abstract: string; background: string; methods: string; results: string; discussion: string; processingStatus: string; pageCount: number; sourceFileName: string; createdAt: string; updatedAt: string }>; total: number; limit: number; offset: number };
export type PapersCreateResponse = { data: { id: string; title: string; authors: Array<string>; year: number; venue: string; doi: string; abstract: string; background: string; methods: string; results: string; discussion: string; processingStatus: string; processingError: string; pageCount: number; sourceFileName: string; createdAt: string; updatedAt: string } };
export type PapersByPaperIdDeleteResponse = { success: boolean; deletedPaperId: string };
export type PapersByPaperIdGetResponse = { data: { id: string; title: string; authors: Array<string>; year: number; venue: string; doi: string; abstract: string; background: string; methods: string; results: string; discussion: string; processingStatus: string; processingError: string; pageCount: number; sourceFileName: string; fullText: string; pages: Array<{ pageNumber: number; text: string }>; createdAt: string; updatedAt: string } };
export type QaAskCreateResponse = { data: { id: string; question: string; answer: string; scope: { paperIds: Array<string>; includeAnnotations: boolean }; hits: Array<{ paperId: string; paperTitle: string; score: number }>; citations: Array<{ paperId: string; paperTitle: string; pageNumber: number; section: string; quote: string; startOffset: number; endOffset: number }>; createdAt: string } };
export type ReportsListResponse = { data: Array<{ id: string; title: string; template: string; status: string; paperIds: Array<string>; paperCount: number; createdAt: string; updatedAt: string }>; total: number; limit: number; offset: number };
export type ReportsCreateResponse = { data: { id: string; title: string; template: string; status: string; paperIds: Array<string>; researchQuestion: string; language: string; createdAt: string; updatedAt: string } };
export type ReportsByReportIdGetResponse = { data: { id: string; title: string; template: string; status: string; error: string; paperIds: Array<string>; researchQuestion: string; language: string; sections: Array<{ key: string; title: string; content: string; citations: Array<{ paperId: string; paperTitle: string; pageNumber: number; section: string; quote: string; startOffset: number; endOffset: number }> }>; createdAt: string; updatedAt: string } };
export type ReportsByReportIdExportCreateResponse = { data: { reportId: string; fileName: string; mimeType: string; encoding: string; contentBase64: string; generatedAt: string } };
export type SettingsAiListResponse = { data: { provider: string; baseUrl: string; model: string; hasApiKey: boolean; maskedApiKey: string; updatedAt: string } };
export type SettingsAiUpdateResponse = { data: { provider: string; baseUrl: string; model: string; hasApiKey: boolean; maskedApiKey: string; updatedAt: string } };

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
  if (!res.ok) { const errText = await res.text().catch(() => ''); let detail = errText; try { detail = JSON.parse(errText).error || errText; } catch {} throw new Error(`${method} ${path} failed: HTTP ${res.status}${detail ? ` - ${detail}` : ''}`); };
  const text = await res.text();
  return (text ? JSON.parse(text) : {}) as T;
}

/** GET /api/annotations — 按论文、关键词或页码检索批注 */
export function annotationsList<T = AnnotationsListResponse>(query?: Record<string, unknown>): Promise<T> {
  return request<T>("GET", '/api/annotations', undefined, query);
}

/** POST /api/annotations — 为论文创建可定位批注 */
export function annotationsCreate<T = AnnotationsCreateResponse>(body: {
  paperId: string; /** 关联论文 ID */
  content: string; /** 批注正文 */
  pageNumber: number; /** PDF 页码，从 1 开始 */
  section?: string; /** 章节名，可选 */
  quote?: string; /** 用于快速定位的原文短片段 */
  startOffset?: number; /** 提取全文中的起始字符偏移 */
  endOffset?: number; /** 提取全文中的结束字符偏移 */
  color?: string; /** 标记颜色语义，默认 yellow */
}): Promise<T> {
  return request<T>("POST", '/api/annotations', body);
}

/** DELETE /api/annotations/{annotationId} — 删除批注 */
export function annotationsByAnnotationIdDelete<T = AnnotationsByAnnotationIdDeleteResponse>(annotationId: string | number): Promise<T> {
  return request<T>("DELETE", `/api/annotations/${annotationId}`, undefined);
}

/** GET /api/annotations/{annotationId} — 获取单条批注及论文定位信息 */
export function annotationsByAnnotationIdGet<T = AnnotationsByAnnotationIdGetResponse>(annotationId: string | number): Promise<T> {
  return request<T>("GET", `/api/annotations/${annotationId}`, undefined);
}

/** PUT /api/annotations/{annotationId} — 更新批注内容与定位信息 */
export function annotationsByAnnotationIdUpdate<T = AnnotationsByAnnotationIdUpdateResponse>(annotationId: string | number, body: {
  content?: string; /** 新的批注正文 */
  pageNumber?: number; /** 新的 PDF 页码 */
  section?: string; /** 新的章节名 */
  quote?: string; /** 新的原文定位片段 */
  startOffset?: number; /** 新的起始字符偏移 */
  endOffset?: number; /** 新的结束字符偏移 */
  color?: string; /** 新的标记颜色语义 */
}): Promise<T> {
  return request<T>("PUT", `/api/annotations/${annotationId}`, body);
}

/** GET /api/papers — 检索并分页列出文献库论文 */
export function papersList<T = PapersListResponse>(query?: Record<string, unknown>): Promise<T> {
  return request<T>("GET", '/api/papers', undefined, query);
}

/** POST /api/papers — 将浏览器本地提取的 PDF 文本与元数据入库并启动结构化研析 */
export function papersCreate<T = PapersCreateResponse>(body: {
  title: string; /** 论文标题 */
  authors: unknown[]; /** 作者姓名字符串数组，可为空数组 */
  year?: number; /** 发表年份 */
  venue?: string; /** 期刊、会议或来源 */
  doi?: string; /** DOI，可选 */
  sourceFileName: string; /** 仅保存原 PDF 文件名，不保存本地绝对路径 */
  pageCount: number; /** PDF 总页数 */
  fullText: string; /** 浏览器从 PDF 提取的全文，不包含 PDF 二进制 */
  pages: unknown[]; /** 页级文本对象数组，每项含 pageNumber 与 text，用于定位 */
}): Promise<T> {
  return request<T>("POST", '/api/papers', body);
}

/** DELETE /api/papers/{paperId} — 删除论文及其关联批注 */
export function papersByPaperIdDelete<T = PapersByPaperIdDeleteResponse>(paperId: string | number): Promise<T> {
  return request<T>("DELETE", `/api/papers/${paperId}`, undefined);
}

/** GET /api/papers/{paperId} — 获取论文详情、结构化研析内容与页级定位文本 */
export function papersByPaperIdGet<T = PapersByPaperIdGetResponse>(paperId: string | number): Promise<T> {
  return request<T>("GET", `/api/papers/${paperId}`, undefined);
}

/** POST /api/qa/ask — 在全部或指定论文范围内问答并返回可核验定位线索 */
export function qaAskCreate<T = QaAskCreateResponse>(body: {
  question: string; /** 用户问题 */
  paperIds?: unknown[]; /** 可选论文 ID 数组；省略或空数组表示全部就绪论文 */
  includeAnnotations?: boolean; /** 是否将相关批注纳入上下文，默认 true */
}): Promise<T> {
  return request<T>("POST", '/api/qa/ask', body);
}

/** GET /api/reports — 分页查询系统文献汇报记录 */
export function reportsList<T = ReportsListResponse>(query?: Record<string, unknown>): Promise<T> {
  return request<T>("GET", '/api/reports', undefined, query);
}

/** POST /api/reports — 按模板和论文范围生成系统文献汇报 */
export function reportsCreate<T = ReportsCreateResponse>(body: {
  title: string; /** 报告标题 */
  template: string; /** 模板标识：systematic-review/comparison/evidence-summary */
  paperIds: unknown[]; /** 参与报告生成的论文 ID 数组，不能为空 */
  researchQuestion?: string; /** 可选，报告聚焦的研究问题 */
  language?: string; /** 报告语言，默认 zh-CN */
}): Promise<T> {
  return request<T>("POST", '/api/reports', body);
}

/** GET /api/reports/{reportId} — 获取报告生成状态、模板化章节与引用线索 */
export function reportsByReportIdGet<T = ReportsByReportIdGetResponse>(reportId: string | number): Promise<T> {
  return request<T>("GET", `/api/reports/${reportId}`, undefined);
}

/** POST /api/reports/{reportId}/export — 将已完成报告导出为 Word DOCX */
export function reportsByReportIdExportCreate<T = ReportsByReportIdExportCreateResponse>(reportId: string | number, body: {
  fileName?: string; /** 可选下载文件名，不含本地路径 */
}): Promise<T> {
  return request<T>("POST", `/api/reports/${reportId}/export`, body);
}

/** GET /api/settings/ai — 获取 AI API 配置状态（不返回明文密钥） */
export function settingsAiList<T = SettingsAiListResponse>(): Promise<T> {
  return request<T>("GET", '/api/settings/ai', undefined);
}

/** PUT /api/settings/ai — 保存用户自己的 AI API 配置 */
export function settingsAiUpdate<T = SettingsAiUpdateResponse>(body: {
  provider?: string; /** 供应商标识，默认 openai-compatible */
  baseUrl: string; /** OpenAI 兼容 API Base URL，例如 https://api.openai.com/v1 */
  model: string; /** 模型名称 */
  apiKey?: string; /** 用户自己的 API Key；为空则保留原 key */
  clearApiKey?: boolean; /** 是否清除已保存 API Key */
}): Promise<T> {
  return request<T>("PUT", '/api/settings/ai', body);
}
