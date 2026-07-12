import { create } from 'zustand';
import type { NotebookType, NotebookSchema, QueryResponse } from '@/types/notebook';
import * as notebookApi from '@/api/notebooks';

interface NotebookState {
  // 当前笔记本
  currentType: NotebookType | null;
  schema: NotebookSchema | null;

  // 数据
  entries: Record<string, any>[];
  total: number;
  page: number;
  pageSize: number;

  // 筛选
  filterJson: string | null;
  orderBy: string;
  orderDir: 'asc' | 'desc';

  // 加载状态
  loading: boolean;
  error: string | null;

  // 操作
  setCurrentType: (type: NotebookType) => Promise<void>;
  fetchEntries: () => Promise<void>;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  setFilter: (filter: string | null) => void;
  setOrder: (by: string, dir: 'asc' | 'desc') => void;
  addEntries: (entries: Record<string, any>[]) => Promise<void>;
  updateEntry: (id: string, updates: Record<string, any>) => Promise<void>;
  deleteEntries: (ids: string[]) => Promise<void>;
  clearError: () => void;
}

export const useNotebookStore = create<NotebookState>((set, get) => ({
  currentType: null,
  schema: null,
  entries: [],
  total: 0,
  page: 1,
  pageSize: 20,
  filterJson: null,
  orderBy: 'created_at',
  orderDir: 'desc',
  loading: false,
  error: null,

  setCurrentType: async (type: NotebookType) => {
    try {
      set({ loading: true, error: null, currentType: type, page: 1 });
      const schema = await notebookApi.getSchema(type);
      set({ schema });
      await get().fetchEntries();
    } catch (e: any) {
      set({ error: e.message || '加载失败' });
    } finally {
      set({ loading: false });
    }
  },

  fetchEntries: async () => {
    const { currentType, page, pageSize, filterJson, orderBy, orderDir } = get();
    if (!currentType) return;
    try {
      set({ loading: true, error: null });
      const res: QueryResponse = await notebookApi.queryEntries(currentType, {
        filter: filterJson || undefined,
        page,
        page_size: pageSize,
        order_by: orderBy,
        order_dir: orderDir,
      });
      set({ entries: res.entries, total: res.total });
    } catch (e: any) {
      set({ error: e.message || '查询失败' });
    } finally {
      set({ loading: false });
    }
  },

  setPage: (page: number) => {
    set({ page });
    get().fetchEntries();
  },

  setPageSize: (size: number) => {
    set({ pageSize: size, page: 1 });
    get().fetchEntries();
  },

  setFilter: (filter: string | null) => {
    set({ filterJson: filter, page: 1 });
    get().fetchEntries();
  },

  setOrder: (by: string, dir: 'asc' | 'desc') => {
    set({ orderBy: by, orderDir: dir });
    get().fetchEntries();
  },

  addEntries: async (entries: Record<string, any>[]) => {
    const { currentType } = get();
    if (!currentType) return;
    try {
      set({ error: null });
      await notebookApi.addEntries(currentType, { entries });
      await get().fetchEntries();
    } catch (e: any) {
      set({ error: e.message || '添加失败' });
      throw e;
    }
  },

  updateEntry: async (id: string, updates: Record<string, any>) => {
    const { currentType } = get();
    if (!currentType) return;
    try {
      set({ error: null });
      await notebookApi.updateEntry(currentType, { id, updates });
      await get().fetchEntries();
    } catch (e: any) {
      set({ error: e.message || '更新失败' });
      throw e;
    }
  },

  deleteEntries: async (ids: string[]) => {
    const { currentType } = get();
    if (!currentType) return;
    try {
      set({ error: null });
      await notebookApi.deleteEntries(currentType, ids);
      await get().fetchEntries();
    } catch (e: any) {
      set({ error: e.message || '删除失败' });
      throw e;
    }
  },

  clearError: () => set({ error: null }),
}));
