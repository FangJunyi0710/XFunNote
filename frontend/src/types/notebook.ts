// 笔记本核心类型
// 对应 backend/schemas.py 中的 Pydantic 模型

import type { NotebookType } from '@/config/notebook';

// ── Schema 相关 ────────────────────────────────────────────

/** Schema 中单个列的描述 */
export interface ColumnDef {
  name: string;
  type: string;
  required: boolean;
  default: string | number | boolean | null;
}

/** 完整的笔记本 Schema */
export interface NotebookSchema {
  table_name: string;
  label: string;
  description: string;
  columns: ColumnDef[];
  display_order: string[];
}

// ── API 请求/响应 ──────────────────────────────────────────

export interface QueryResponse {
  entries: Record<string, unknown>[];
  total: number;
  page?: number;
  page_size?: number;
}

export interface AddRequest {
  entries: Record<string, unknown>[];
}

export interface UpdateRequest {
  id: string;
  updates: Record<string, unknown>;
}

export interface DeletePreview {
  id: string;
  summary: string;
}

export interface DeleteResponse {
  count: number;
  results: Record<string, unknown>[];
}
