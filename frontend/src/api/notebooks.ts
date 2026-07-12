import { api } from './client';
import type {
  NotebookSchema,
  QueryResponse,
  AddRequest,
  UpdateRequest,
  DeletePreview,
  DeleteResponse,
  NotebookType,
} from '@/types/notebook';

const NOTEBOOK_MAP: Record<NotebookType, string> = {
  plan: 'plan',
  diary: 'diary',
  word: 'word',
  accumulation: 'accumulation',
  aimemory: 'aimemory',
};

export async function listNotebooks(): Promise<NotebookSchema[]> {
  return api.get<NotebookSchema[]>('/notebooks');
}

export async function getSchema(type: NotebookType): Promise<NotebookSchema> {
  return api.get<NotebookSchema>(`/notebooks/${NOTEBOOK_MAP[type]}/schema`);
}

/**
 * 构建默认的 View JSON（显示所有列，无筛选条件）。
 * 后端要求 view 参数必填，格式为 `{表名: [{columns, filter}]}`。
 */
function buildDefaultView(type: NotebookType, filter?: string): string {
  const tableName = NOTEBOOK_MAP[type];
  let filterJson: string;
  if (filter) {
    filterJson = filter;
  } else {
    // 无筛选：使用 op=TRUE 作为永真条件
    filterJson = JSON.stringify({ column: '_', value: '_', op: 'TRUE' });
  }
  return JSON.stringify({
    [tableName]: [{ columns: ['*'], filter: JSON.parse(filterJson) }],
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
  queryParams.view = buildDefaultView(type, params?.filter);

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
  data: AddRequest,
): Promise<{ message: string; ids: string[] }> {
  return api.post(`/notebooks/${NOTEBOOK_MAP[type]}/entries`, data);
}

export async function updateEntry(
  type: NotebookType,
  data: UpdateRequest,
): Promise<{ message: string }> {
  return api.put(`/notebooks/${NOTEBOOK_MAP[type]}/entries`, data);
}

export async function previewDelete(
  type: NotebookType,
  ids: string[],
): Promise<DeletePreview[]> {
  return api.post<DeletePreview[]>(
    `/notebooks/${NOTEBOOK_MAP[type]}/entries/delete-preview`,
    { ids },
  );
}

export async function deleteEntries(
  type: NotebookType,
  ids: string[],
): Promise<DeleteResponse> {
  return api.delete<DeleteResponse>(
    `/notebooks/${NOTEBOOK_MAP[type]}/entries`,
    { ids: ids.join(',') } as any,
  );
}

// Hack: need to send body in DELETE
export async function deleteEntriesWithBody(
  type: NotebookType,
  ids: string[],
): Promise<DeleteResponse> {
  const res = await fetch(
    `${window.location.origin}/api/v1/notebooks/${NOTEBOOK_MAP[type]}/entries`,
    {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids }),
    },
  );
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}
