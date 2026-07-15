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
