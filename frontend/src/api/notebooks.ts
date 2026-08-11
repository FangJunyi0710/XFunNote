import { api } from '@/api/client';
import type {
  NotebookSchema,
  ColumnDef,
  Entry,
  OrderBy,
} from '@/types/notebook';
import { sortColumns, type NotebookType } from '@/config/notebook';
import type { Filter, View } from '@/types/filter';

/** 后端 list 路由返回的原始格式 */
interface RawColumn {
  name: string;
  col_type: string;
  nullable: boolean;
  default: boolean;
  auto: boolean;
}

interface RawNotebookSchema {
  table_name: string;
  columns: RawColumn[];
}

const convertColumns = (raw: RawColumn[]): ColumnDef[] =>
  sortColumns(raw.map(col => ({
    name: col.name,
    type: col.col_type,
    required: !col.nullable && (col.default === null) && !col.auto,
    auto: col.auto,
  })));

/** 获取笔记本列表（后端一次返回所有 schema，前端组装为 NotebookSchema[]） */
export const listNotebooks = async (): Promise<NotebookSchema[]> => {
  const rawList = await api.get<RawNotebookSchema[]>('/notebooks');
  return rawList.map(raw => ({
    name: raw.table_name as NotebookType,
    columns: convertColumns(raw.columns)
  }));
}

/** 获取笔记本 Schema（后端返回列定义，前端组装为完整 NotebookSchema） */
export const getSchema = async (type: NotebookType): Promise<NotebookSchema> => {
  const rawColumns = await api.get<RawColumn[]>(`/notebooks/${type}/schema`);
  return {
    name: type,
    columns: convertColumns(rawColumns),
  };
}

interface EntriesResponse {
  count: number;
  results: Entry[];
}

export const queryEntries = async(
  type: NotebookType,
  params: {
    view: View;
    filter?: Filter;
    limit: number;
    offset?: number;
    order_by?: OrderBy;
  },
): Promise<EntriesResponse> => {
  const queryParams: Record<string, string> = {};

  // 参数映射：前端 offset/limit → 后端 offset/limit
  params.offset = params.offset ?? 0;
  const offset = Math.max(0, params.offset);
  const limit = params.limit + params.offset - offset;
  queryParams['offset'] = String(offset);
  queryParams['limit'] = String(limit);

  // 参数映射：前端 order_by → 后端 order_by
  queryParams['order_by'] = params.order_by?.map(([col, dir]) => `${col} ${dir}`).join(", ") ?? "";

  const combinedView: View = {[type]: params.view[type]?.map(([cols, flt]) => [cols, [[flt, params.filter ?? [[]]]]]) ?? []};
  queryParams['view'] = JSON.stringify(combinedView);

  // 响应映射：后端 { count, results } → 前端 { total, entries, offset, limit }
  return await api.get<{ count: number; results: Entry[] }>(
    `/notebooks/${type}/entries`,
    queryParams,
  );
}

export const addEntries = async(
  type: NotebookType,
  entries: Entry[]
): Promise<EntriesResponse> =>
  api.post(`/notebooks/${type}/entries`, {entries});

export const updateEntries = async(
  type: NotebookType,
  ids: string[],
  values: Entry
): Promise<EntriesResponse> =>
  // 前端格式 { id, updates } → 后端格式 { filter: [[{column, op, value}]], values }
  api.put(`/notebooks/${type}/entries`, {
    filter: { column: 'id', op: 'IN', value: ids },
    values
  });

export const deleteEntries = async(
  type: NotebookType,
  ids: string[],
): Promise<EntriesResponse> =>
  // 前端 ids 列表 → 后端 filter: [[{column, op, value}]]
  api.delete(
    `/notebooks/${type}/entries`,
    { filter: { column: 'id', op: 'IN', value: ids } },
  );
