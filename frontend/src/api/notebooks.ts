import { api } from './client';
import type {
  NotebookSchema,
  ColumnDef,
} from '@/types/notebook';
import type {
  QueryResponse,
  UpdateRequest,
  DeleteResponse,
} from '@/types/notebook';
import type { NotebookType } from '@/config/notebook';
import { NOTEBOOK_INFO } from '@/config/notebook';

/** 获取笔记本列表（后端返回名称列表，前端组装为 NotebookSchema[]） */
export async function listNotebooks(): Promise<NotebookSchema[]> {
  const names = await api.get<string[]>('/notebooks');
  return Promise.all(names.map((name) => getSchema(name as NotebookType)));
}

/** 获取笔记本 Schema（后端返回列定义，前端组装为完整 NotebookSchema） */
export async function getSchema(type: NotebookType): Promise<NotebookSchema> {
  // 后端 Column.asdict() 返回字段：name, col_type, nullable, primary_key, unique, index, auto
  const rawColumns = await api.get<any[]>(`/notebooks/${type}/schema`);
  const columns: ColumnDef[] = rawColumns.map((col) => ({
    name: col.name,
    type: col.col_type,        // 映射 col_type → type
    required: !col.nullable,   // 取反：nullable=false → required=true
    default: col.default ?? null,
  }));
  const info = NOTEBOOK_INFO[type] || { label: type, description: '' };
  return {
    table_name: type,
    ...info,
    columns,
    display_order: columns.map((c) => c.name),
  };
}

/**
 * 构建默认的 View JSON。
 * 后端要求 view 参数必填，格式为 `{表名: [{columns, filter}]}`。
 * filter 格式：单个 Condition: {column, op, value} 或 DNF: [[{column, op, value}, ...], ...]
 * @param columns 完整列名列表。传入时使用实际列名。
 */
function buildDefaultView(type: NotebookType, columns: string[], filter?: string): string {
  const tableName = type;
  let filterJson: any;
  if (filter) {
    filterJson = JSON.parse(filter);
  } else {
    // 无筛选：使用 op=TRUE 作为永真条件
    filterJson = { column: '_', value: '_', op: 'TRUE' };
  }
  const viewColumns = columns;
  return JSON.stringify({
    [tableName]: [{ columns: viewColumns, filter: filterJson }],
  });
}

export async function queryEntries(
  type: NotebookType,
  params: {
    filter?: string;
    page?: number;
    page_size?: number;
    order_by?: string;
    order_dir?: string;
    columns: string[];
  },
): Promise<QueryResponse> {
  const queryParams: Record<string, string> = {};

  // 参数映射：前端 page/page_size → 后端 offset/limit
  const page = params.page ?? 1;
  const pageSize = params.page_size ?? 20;
  queryParams.offset = String((page - 1) * pageSize);
  queryParams.limit = String(pageSize);

  // 参数映射：前端 order_by + order_dir → 后端 order_by
  if (params.order_by) {
    queryParams.order_by = `${params.order_by} ${(params.order_dir || 'asc').toUpperCase()}`.trim();
  }

  // view 是后端必填参数，自动生成默认视图
  queryParams.view = buildDefaultView(type, params.columns, params.filter);

  // 响应映射：后端 { count, results } → 前端 { total, entries, page, page_size }
  const res = await api.get<{ count: number; results: Record<string, any>[] }>(
    `/notebooks/${type}/entries`,
    queryParams,
  );
  return {
    total: res.count,
    entries: res.results,
    page,
    page_size: pageSize,
  };
}

export async function addEntries(
  type: NotebookType,
  data: { entries: Record<string, any>[] },
): Promise<{ count: number; results: Record<string, any>[] }> {
  return api.post(`/notebooks/${type}/entries`, data);
}

export async function updateEntry(
  type: NotebookType,
  data: UpdateRequest,
): Promise<{ count: number; results: Record<string, any>[] }> {
  // 前端格式 { id, updates } → 后端格式 { filter: [[{column, op, value}]], values }
  return api.put(`/notebooks/${type}/entries`, {
    filter: [[{ column: 'id', op: '=', value: data.id }]],
    values: data.updates,
  });
}

/** 批量更新条目（按 ID 列表 + 统一的值） */
export async function batchUpdateEntries(
  type: NotebookType,
  ids: string[],
  values: Record<string, any>,
): Promise<{ count: number; results: Record<string, any>[] }> {
  return api.put(`/notebooks/${type}/entries`, {
    filter: [[{ column: 'id', op: 'IN', value: ids }]],
    values,
  });
}

export async function deleteEntries(
  type: NotebookType,
  ids: string[],
): Promise<DeleteResponse> {
  // 前端 ids 列表 → 后端 filter: [[{column, op, value}]]
  return api.delete<DeleteResponse>(
    `/notebooks/${type}/entries`,
    { filter: [[{ column: 'id', op: 'IN', value: ids }]] },
  );
}
