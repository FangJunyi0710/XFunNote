import { create } from 'zustand';
import type { NotebookSchema } from '@/types/notebook';
import type { NotebookType } from '@/config/notebook';
import type { QueryResponse } from '@/types/notebook';
import * as notebookApi from '@/api/notebooks';
import { castEntries } from '@/lib/type-guards';
import { handleError } from '@/lib/error';

/** 全局 schema 缓存，避免重复请求 */
let schemaCache: Record<string, NotebookSchema> | null = null;

async function getCachedSchema(type: NotebookType): Promise<NotebookSchema> {
  if (schemaCache?.[type]) {
    return schemaCache[type];
  }
  // 首次调用时拉取全部 schema
  const all = await notebookApi.listNotebooks();
  schemaCache = {};
  for (const s of all) {
    schemaCache[s.table_name] = s;
  }
  return schemaCache[type];
}

// 当用户增删笔记本类型时清空缓存（当前没有此类操作，留作扩展）
export function clearSchemaCache() {
  schemaCache = null;
}

interface NotebookState {
  // 当前笔记本
  currentType: NotebookType | null;
  schema: NotebookSchema | null;

  // 数据
  entries: Record<string, unknown>[];
  total: number;
  offset: number;
  limit: number;

  // 筛选
  filterJson: string | null;
  orderBy: string;
  orderDir: 'asc' | 'desc';

  // 加载状态
  loading: boolean;

  // 操作
  setCurrentType: (type: NotebookType) => Promise<void>;
  fetchEntries: () => Promise<void>;
  setOffset: (offset: number) => void;
  setLimit: (limit: number) => void;
  setFilter: (filter: string | null) => void;
  setOrder: (by: string, dir: 'asc' | 'desc') => void;
  addEntries: (entries: Record<string, unknown>[]) => Promise<void>;
  updateEntry: (id: string, updates: Record<string, unknown>) => Promise<void>;
  batchUpdateEntries: (ids: string[], values: Record<string, unknown>) => Promise<void>;
  deleteEntries: (ids: string[]) => Promise<void>;
}

export const useNotebookStore = create<NotebookState>((set, get) => ({
  currentType: null,
  schema: null,
  entries: [],
  total: 0,
  offset: 0,
  limit: 20,
  filterJson: null,
  orderBy: 'id',
  orderDir: 'desc',
  loading: false,

  setCurrentType: async (type: NotebookType) => {
    try {
      // 先清空旧数据再设置 loading，避免切换时短暂显示先前内容
      set({ loading: true, currentType: type, offset: 0, entries: [], schema: null, filterJson: null });
      const schema = await getCachedSchema(type);
      set({ schema });
      await get().fetchEntries();
    } catch (e: unknown) {
      handleError(e, '加载失败');
    } finally {
      set({ loading: false });
    }
  },

  fetchEntries: async () => {
    const { currentType, schema, offset, limit, filterJson, orderBy, orderDir } = get();
    if (!currentType) return;
    try {
      set({ loading: true });
      const res: QueryResponse = await notebookApi.queryEntries(currentType, {
        filter: filterJson || undefined,
        offset,
        limit,
        order_by: orderBy,
        order_dir: orderDir,
        columns: schema?.display_order ?? [],
      });
      set({ entries: castEntries(res.entries as Record<string, unknown>[], schema?.columns ?? []), total: res.total });
    } catch (e: unknown) {
      handleError(e, '查询失败');
    } finally {
      set({ loading: false });
    }
  },

  setOffset: (offset: number) => {
    set({ offset });
    get().fetchEntries();
  },

  setLimit: (limit: number) => {
    set({ limit, offset: 0 });
    get().fetchEntries();
  },

  setFilter: (filter: string | null) => {
    set({ filterJson: filter, offset: 0 });
    get().fetchEntries();
  },

  setOrder: (by: string, dir: 'asc' | 'desc') => {
    set({ orderBy: by, orderDir: dir });
    get().fetchEntries();
  },

  addEntries: async (entries: Record<string, unknown>[]) => {
    const { currentType } = get();
    if (!currentType) return;
    try {
      await notebookApi.addEntries(currentType, { entries });
      await get().fetchEntries();
    } catch (e: unknown) {
      handleError(e, '添加失败');
      throw e;
    }
  },

  updateEntry: async (id: string, updates: Record<string, unknown>) => {
    const { currentType } = get();
    if (!currentType) return;
    try {
      await notebookApi.updateEntry(currentType, { id, updates });
      await get().fetchEntries();
    } catch (e: unknown) {
      handleError(e, '更新失败');
      throw e;
    }
  },

  batchUpdateEntries: async (ids: string[], values: Record<string, unknown>) => {
    const { currentType } = get();
    if (!currentType) return;
    try {
      await notebookApi.batchUpdateEntries(currentType, ids, values);
      await get().fetchEntries();
    } catch (e: unknown) {
      handleError(e, '批量更新失败');
      throw e;
    }
  },

  deleteEntries: async (ids: string[]) => {
    const { currentType } = get();
    if (!currentType) return;
    try {
      await notebookApi.deleteEntries(currentType, ids);
      await get().fetchEntries();
    } catch (e: unknown) {
      handleError(e, '删除失败');
      throw e;
    }
  },
}));
