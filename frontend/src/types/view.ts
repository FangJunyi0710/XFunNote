// 视图（View） 类型
// 对应 xfun/core/view.py 中的 View / TableSpec

export interface TableSpec {
  table: string;
  columns?: string[];
  filter?: any; // Filter 的 JSON 形式
  order_by?: string;
  order_dir?: 'asc' | 'desc';
  limit?: number;
}

export interface ViewData {
  name: string;
  tables: TableSpec[];
  label?: string;
  description?: string;
  version?: number;
}

export interface ViewFile {
  id: string;
  name: string;
  data: string;
  created_at: string;
  updated_at: string;
}
