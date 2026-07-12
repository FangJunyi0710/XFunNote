// 笔记本核心类型
// 对应 backend/schemas.py 中的 Pydantic 模型

export interface ColumnDef {
  name: string;
  type: string;
  required: boolean;
  default: any;
}

export interface NotebookSchema {
  table_name: string;
  label: string;
  description: string;
  columns: ColumnDef[];
  display_order: string[];
}

// 通用条目核心字段（所有本子共有的字段）
export interface EntryBase {
  id: string;
  created_at: string;
  updated_at: string;
  user_id: string;
}

// ------------------------------------------------
// Plan 笔记本扩展字段
// ------------------------------------------------
export interface PlanEntry extends EntryBase {
  month: string;
  title: string;
  done: boolean | number;
  note: string;
}

// ------------------------------------------------
// Diary 笔记本扩展字段
// ------------------------------------------------
export interface DiaryEntry extends EntryBase {
  date: string;
  content: string;
}

// ------------------------------------------------
// Word 笔记本扩展字段
// ------------------------------------------------
export interface WordEntry extends EntryBase {
  word: string;
  translation: string;
  review_status: string;
  context: string;
}

// ------------------------------------------------
// Accumulation 笔记本扩展字段
// ------------------------------------------------
export interface AccumulationEntry extends EntryBase {
  title: string;
  category: string;
  content: string;
  source: string;
  tags: string;
}

// ------------------------------------------------
// AI Memory 笔记本扩展字段
// ------------------------------------------------
export interface AimemoryEntry extends EntryBase {
  title: string;
  content: string;
  source: string;
}

// 条目联合类型
export type AnyEntry = PlanEntry | DiaryEntry | WordEntry | AccumulationEntry | AimemoryEntry;

// 笔记本类型标识
export type NotebookType = 'plan' | 'diary' | 'word' | 'accumulation' | 'aimemory';

// API 响应
export interface QueryResponse {
  entries: Record<string, any>[];
  total: number;
  page?: number;
  page_size?: number;
}

// 批量操作
export interface AddRequest {
  entries: Record<string, any>[];
}

export interface UpdateRequest {
  id: string;
  updates: Record<string, any>;
}

export interface DeletePreview {
  id: string;
  summary: string;
}

export interface DeleteResponse {
  message: string;
  count: number;
  deleted_ids: string[];
}
