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

// 通用条目核心字段（对应后端 BASE_COLUMNS）
export interface EntryBase {
  id: string;
  content: string;
  tags: string | null;
  is_ai_gen: number;
  ai_tags: string | null;
  ai_note: string | null;
  created_at: string;
  updated_at: string;
  user_id: string;
}

// ------------------------------------------------
// Plan 笔记本扩展字段（对应 plan.py _extra_columns）
// ------------------------------------------------
export interface PlanEntry extends EntryBase {
  no: string;
  seq: number;
  month: string;
  done: boolean | number;
  status: string | null;
}

// ------------------------------------------------
// Diary 笔记本扩展字段（对应 diary.py _extra_columns）
// ------------------------------------------------
export interface DiaryEntry extends EntryBase {
  date: string;
  mood: string | null;
  weather: string | null;
}

// ------------------------------------------------
// Word 笔记本扩展字段（对应 word.py _extra_columns）
// ------------------------------------------------
export interface WordEntry extends EntryBase {
  word: string;
  part_of_speech: string | null;
  phonetic: string | null;
  example: string | null;
  review_count: number;
  performance: number;
  next_review: string | null;
  last_review: string | null;
  related_words: string | null;
}

// ------------------------------------------------
// Accumulation 笔记本扩展字段（对应 accumulation.py _extra_columns）
// ------------------------------------------------
export interface AccumulationEntry extends EntryBase {
  source: string;
  note: string | null;
}

// ------------------------------------------------
// AI Memory 笔记本扩展字段（对应 aimemory.py _extra_columns）
// ------------------------------------------------
export interface AimemoryEntry extends EntryBase {
  title: string;
  source: string;
}

// ------------------------------------------------
// Timeline 笔记本扩展字段
// ------------------------------------------------
export interface TimelineEntry extends EntryBase {
  start_time: string;
  end_time?: string;
  location?: string;
}

// ------------------------------------------------
// Schedule 笔记本扩展字段
// ------------------------------------------------
export interface ScheduleEntry extends EntryBase {
  start_time: string;
  end_time?: string;
  location?: string;
}

// 条目联合类型
export type AnyEntry = PlanEntry | DiaryEntry | WordEntry | AccumulationEntry | AimemoryEntry | TimelineEntry | ScheduleEntry;

// 笔记本类型标识
export type NotebookType = 'plan' | 'diary' | 'word' | 'accumulation' | 'aimemory' | 'timeline' | 'schedule';

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
  count: number;
  results: Record<string, any>[];
}
