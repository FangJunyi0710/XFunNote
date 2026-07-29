import { create } from 'zustand';
import type { NotebookSchema } from '@/types/notebook';
import type { NotebookType } from '@/config/notebook';
import type { QueryResponse } from '@/types/notebook';
import * as notebookApi from '@/api/notebooks';
import { castEntries } from '@/lib/type-guards';
import { handleError } from '@/lib/error';
import { useTokenStore } from '@/stores/tokenStore';

// ── 默认分页大小 ──────────────────────────────────────────────────────
const DEFAULT_PAGE_LIMIT = 20;

// ── 全局 schema 缓存（所有用户共享） ──────────────────────────────────
let schemaCache: Record<string, NotebookSchema> | null = null;

const getCachedSchema = async (type: NotebookType): Promise<NotebookSchema> => {
  if (schemaCache?.[type]) {
    return schemaCache[type];
  }
  const all = await notebookApi.listNotebooks();
  schemaCache = {};
  for (const s of all) {
    schemaCache[s.table_name] = s;
  }
  const result = schemaCache[type];
  if (!result) {
    throw new Error(`Schema not found for type: ${type}`);
  }
  return result;
}

// ── 按用户分页持久化 ──────────────────────────────────────────────────
const getPaginationKey = (userName: string): string => `xfun-notebook-pagination-${userName}`;

interface PaginationCache {
  offset: number;
  limit: number;
}

const loadPagination = (userName: string, type: NotebookType): PaginationCache => {
  try {
    const raw = localStorage.getItem(getPaginationKey(userName));
    if (!raw) return { offset: 0, limit: DEFAULT_PAGE_LIMIT };
    const all: Record<string, PaginationCache> = JSON.parse(raw);
    return all[type] ?? { offset: 0, limit: DEFAULT_PAGE_LIMIT };
  } catch {
    return { offset: 0, limit: DEFAULT_PAGE_LIMIT };
  }
}

const savePagination = (userName: string, type: NotebookType, offset: number, limit: number) => {
  try {
    const key = getPaginationKey(userName);
    const raw = localStorage.getItem(key);
    const all: Record<string, PaginationCache> = raw ? JSON.parse(raw) : {};
    all[type] = { offset, limit };
    localStorage.setItem(key, JSON.stringify(all));
  } catch {
    // ignore
  }
}

// ── Store 状态（按用户隔离） ──────────────────────────────────────────
interface UserNotebookData {
  currentType: NotebookType | null;
  schema: NotebookSchema | null;
  entries: Record<string, unknown>[];
  total: number;
  offset: number;
  limit: number;
  filterJson: string | null;
  orderBy: string;
  orderDir: 'asc' | 'desc';
}

interface NotebookState {
  users: Record<string, UserNotebookData>;
  loading: boolean;
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

const getCurrentUserName = () => useTokenStore.getState().activeUserName;

const defaultUserData = (): UserNotebookData => ({
  currentType: null,
  schema: null,
  entries: [],
  total: 0,
  offset: 0,
  limit: DEFAULT_PAGE_LIMIT,
  filterJson: null,
  orderBy: 'id',
  orderDir: 'desc',
});

export const useNotebookStore = create<NotebookState>((set, get) => ({
  users: {},
  loading: false,

  ensureUser: () => {
    const userName = getCurrentUserName();
    if (!userName) return null;
    set((state) => {
      if (!state.users[userName]) {
        return { users: { ...state.users, [userName]: defaultUserData() } };
      }
      return state;
    });
    return userName;
  },

  setCurrentType: async (type: NotebookType) => {
    const userName = getCurrentUserName();
    if (!userName) {
      handleError(new Error('未选择用户'), '加载失败');
      return;
    }
    if (!get().users[userName]) {
      set((state) => ({ users: { ...state.users, [userName]: defaultUserData() } }));
    }

    try {
      const { offset, limit } = loadPagination(userName, type);
      set((state) => {
        const existing = state.users[userName];
        return {
          users: {
            ...state.users,
            [userName]: existing
              ? {
                  ...existing,
                  currentType: type,
                  offset,
                  limit,
                  entries: [],
                  schema: null,
                  filterJson: null,
                }
              : {
                  ...defaultUserData(),
                  currentType: type,
                  offset,
                  limit,
                },
          },
          loading: true,
        };
      });

      const schema = await getCachedSchema(type);
      set((state) => {
        const existing = state.users[userName];
        return {
          users: {
            ...state.users,
            [userName]: existing
              ? { ...existing, schema }
              : { ...defaultUserData(), schema, currentType: type },
          },
        };
      });

      await get().fetchEntries();
    } catch (e: unknown) {
      handleError(e, '加载失败');
    } finally {
      set({ loading: false });
    }
  },

  fetchEntries: async () => {
    const userName = getCurrentUserName();
    if (!userName) return;
    const userData = get().users[userName];
    if (!userData || !userData.currentType) return;
    const { currentType, schema, offset, limit, filterJson, orderBy, orderDir } = userData;
    try {
      set({ loading: true });
      const queryParams: Parameters<typeof notebookApi.queryEntries>[1] = {
        offset,
        limit,
        order_by: orderBy,
        order_dir: orderDir,
        columns: schema?.display_order ?? [],
      };
      if (filterJson !== null && filterJson !== undefined) {
        queryParams.filter = filterJson;
      }
      const res: QueryResponse = await notebookApi.queryEntries(currentType, queryParams);
      set((state) => {
        const existing = state.users[userName];
        return {
          users: {
            ...state.users,
            [userName]: existing
              ? {
                  ...existing,
                  entries: castEntries(res.entries as Record<string, unknown>[], schema?.columns ?? []),
                  total: res.total,
                }
              : {
                  ...defaultUserData(),
                  entries: castEntries(res.entries as Record<string, unknown>[], schema?.columns ?? []),
                  total: res.total,
                },
          },
        };
      });
    } catch (e: unknown) {
      handleError(e, '查询失败');
    } finally {
      set({ loading: false });
    }
  },

  setOffset: (offset: number) => {
    const userName = getCurrentUserName();
    if (!userName) return;
    const userData = get().users[userName];
    if (!userData) return;
    const { currentType, limit } = userData;
    set((state) => {
      const existing = state.users[userName];
      return {
        users: {
          ...state.users,
          [userName]: existing ? { ...existing, offset } : { ...defaultUserData(), offset },
        },
      };
    });
    if (currentType) {
      savePagination(userName, currentType, offset, limit);
    }
    get().fetchEntries();
  },

  setLimit: (limit: number) => {
    const userName = getCurrentUserName();
    if (!userName) return;
    const userData = get().users[userName];
    if (!userData) return;
    const { currentType, offset } = userData;
    set((state) => {
      const existing = state.users[userName];
      return {
        users: {
          ...state.users,
          [userName]: existing ? { ...existing, limit } : { ...defaultUserData(), limit },
        },
      };
    });
    if (currentType) {
      savePagination(userName, currentType, offset, limit);
    }
    get().fetchEntries();
  },

  setFilter: (filter: string | null) => {
    const userName = getCurrentUserName();
    if (!userName) return;
    set((state) => {
      const existing = state.users[userName];
      return {
        users: {
          ...state.users,
          [userName]: existing
            ? { ...existing, filterJson: filter, offset: 0 }
            : { ...defaultUserData(), filterJson: filter, offset: 0 },
        },
      };
    });
    get().fetchEntries();
  },

  setOrder: (by: string, dir: 'asc' | 'desc') => {
    const userName = getCurrentUserName();
    if (!userName) return;
    set((state) => {
      const existing = state.users[userName];
      return {
        users: {
          ...state.users,
          [userName]: existing
            ? { ...existing, orderBy: by, orderDir: dir }
            : { ...defaultUserData(), orderBy: by, orderDir: dir },
        },
      };
    });
    get().fetchEntries();
  },

  addEntries: async (entries: Record<string, unknown>[]) => {
    const userName = getCurrentUserName();
    if (!userName) return;
    const userData = get().users[userName];
    if (!userData || !userData.currentType) return;
    try {
      await notebookApi.addEntries(userData.currentType, { entries });
      await get().fetchEntries();
    } catch (e: unknown) {
      handleError(e, '添加失败');
      throw e;
    }
  },

  updateEntry: async (id: string, updates: Record<string, unknown>) => {
    const userName = getCurrentUserName();
    if (!userName) return;
    const userData = get().users[userName];
    if (!userData || !userData.currentType) return;
    try {
      await notebookApi.updateEntry(userData.currentType, { id, updates });
      await get().fetchEntries();
    } catch (e: unknown) {
      handleError(e, '更新失败');
      throw e;
    }
  },

  batchUpdateEntries: async (ids: string[], values: Record<string, unknown>) => {
    const userName = getCurrentUserName();
    if (!userName) return;
    const userData = get().users[userName];
    if (!userData || !userData.currentType) return;
    try {
      await notebookApi.batchUpdateEntries(userData.currentType, ids, values);
      await get().fetchEntries();
    } catch (e: unknown) {
      handleError(e, '批量更新失败');
      throw e;
    }
  },

  deleteEntries: async (ids: string[]) => {
    const userName = getCurrentUserName();
    if (!userName) return;
    const userData = get().users[userName];
    if (!userData || !userData.currentType) return;
    try {
      await notebookApi.deleteEntries(userData.currentType, ids);
      await get().fetchEntries();
    } catch (e: unknown) {
      handleError(e, '删除失败');
      throw e;
    }
  },
}));

export const useCurrentNotebookData = () => {
  const userName = useTokenStore((s) => s.activeUserName);
  return useNotebookStore((s) => (userName ? s.users[userName] : null));
};
