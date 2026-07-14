import { api } from './client';
import type {
  NotebookSchema,
  QueryResponse,
  UpdateRequest,
  DeleteResponse,
  NotebookType,
  ColumnDef,
} from '@/types/notebook';

const NOTEBOOK_MAP: Record<NotebookType, string> = {
  plan: 'plan',
  diary: 'diary',
  word: 'word',
  accumulation: 'accumulation',
  aimemory: 'aimemory',
  timeline: 'timeline',
  schedule: 'schedule',
};

/** 静态笔记本元信息（后端不返回 label / description） */
const NOTEBOOK_INFO: Record<string, { label: string; description: string }> = {
  plan: { label: '计划', description: '管理月度计划与任务' },
  diary: { label: '日记', description: '记录每日生活与感悟' },
  word: { label: '单词', description: '单词学习与复习' },
  accumulation: { label: '积累', description: '知识碎片整理与沉淀' },
  aimemory: { label: 'AI 记忆', description: 'AI 自动记录的关键信息' },
  timeline: { label: '时间线', description: '记录实际时间花费' },
  schedule: { label: '日程', description: '规划未来日程' },
};

/** 获取笔记本列表（后端返回名称列表，前端组装为 NotebookSchema[]） */
export async function listNotebooks(): Promise<NotebookSchema[]> {
  const names = await api.get<string[]>('/notebooks');
  return Promise.all(names.map((name) => getSchema(name as NotebookType)));
}

/** 获取笔记本 Schema（后端返回列定义，前端组装为完整 NotebookSchema） */
export async function getSchema(type: NotebookType): Promise<NotebookSchema> {
  // 后端 Column.asdict() 返回字段：name, col_type, nullable, primary_key, unique, index, auto
  const rawColumns = await api.get<any[]>(`/notebooks/${NOTEBOOK_MAP[type]}/schema`);
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
 * @param columns 可选，完整列名列表。传入时使用实际列名，否则使用 ['*']（需后端支持通配展开）。
 */
function buildDefaultView(type: NotebookType, filter?: string, columns?: string[]): string {
  const tableName = NOTEBOOK_MAP[type];
  let filterJson: any;
  if (filter) {
    filterJson = JSON.parse(filter);
  } else {
    // 无筛选：使用 op=TRUE 作为永真条件
    filterJson = { column: '_', value: '_', op: 'TRUE' };
  }
  const viewColumns = columns && columns.length > 0 ? columns : ['*'];
  return JSON.stringify({
    [tableName]: [{ columns: viewColumns, filter: filterJson }],
  });
}

export async function queryEntries(
  type: NotebookType,
  params?: {
    filter?: string;
    page?: number;
    page_size?: number;
    order_by?: string;
    order_dir?: string;
    columns?: string[];
  },
): Promise<QueryResponse> {
  const queryParams: Record<string, string> = {};

  // 参数映射：前端 page/page_size → 后端 offset/limit
  const page = params?.page ?? 1;
  const pageSize = params?.page_size ?? 20;
  queryParams.offset = String((page - 1) * pageSize);
  queryParams.limit = String(pageSize);

  // 参数映射：前端 order_by + order_dir → 后端 order_by
  if (params?.order_by) {
    queryParams.order_by = `${params.order_by} ${(params.order_dir || 'asc').toUpperCase()}`.trim();
  }

  // view 是后端必填参数，自动生成默认视图
  queryParams.view = buildDefaultView(type, params?.filter, params?.columns);

  // 响应映射：后端 { count, results } → 前端 { total, entries, page, page_size }
  const res = await api.get<{ count: number; results: Record<string, any>[] }>(
    `/notebooks/${NOTEBOOK_MAP[type]}/entries`,
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
  return api.post(`/notebooks/${NOTEBOOK_MAP[type]}/entries`, data);
}

export async function updateEntry(
  type: NotebookType,
  data: UpdateRequest,
): Promise<{ count: number; results: Record<string, any>[] }> {
  // 前端格式 { id, updates } → 后端格式 { filter: [[{column, op, value}]], values }
  return api.put(`/notebooks/${NOTEBOOK_MAP[type]}/entries`, {
    filter: [[{ column: 'id', op: '=', value: data.id }]],
    values: data.updates,
  });
}

export async function deleteEntries(
  type: NotebookType,
  ids: string[],
): Promise<DeleteResponse> {
  // 前端 ids 列表 → 后端 filter: [[{column, op, value}]]
  return api.delete<DeleteResponse>(
    `/notebooks/${NOTEBOOK_MAP[type]}/entries`,
    { filter: [[{ column: 'id', op: 'IN', value: ids }]] },
  );
}
