import { create } from 'zustand';
import { type Entry, type NotebookSchema, type OrderBy } from '@/types/notebook';
import type { NotebookType } from '@/config/notebook';
import { handleError } from '@/lib/error';
import { useTokenStore } from '@/stores/tokenStore';
import { addEntries, deleteEntries, getSchema, queryEntries, updateEntries } from '@/api/notebooks';
import type { Filter, View } from '@/types/filter';

// ── 默认分页大小 ──────────────────────────────────────────────────────
export const DEFAULT_PAGE_LIMIT = 20;

// ── 全局 schema 缓存（所有用户共享） ──────────────────────────────────
let schemaCache: Partial<Record<NotebookType, NotebookSchema>> = {};

const getCachedSchema = async (type: NotebookType): Promise<NotebookSchema> => {
  if (schemaCache[type]) {
    return schemaCache[type];
  }
  const schema = await getSchema(type);
  schemaCache[schema.name] = schema;
  return schema;
}

// ── Store 状态（按用户隔离） ──────────────────────────────────────────
interface UserNotebookData {
  view: View,
  type: NotebookType | null;
  schema: NotebookSchema | null;
  entries: Entry[];
  total: number;
  loaded: boolean;
  offset: number;
  limit: number;
  filter: Filter;
  order_by: OrderBy;
}
// TODO 前端实现真正的视图筛选

const getCurrentUserName = () => useTokenStore.getState().activeUserName;

const defaultUserData = (): UserNotebookData => ({
  view: {},
  type: null,
  schema: null,
  entries: [],
  total: 0,
  loaded: false,
  offset: 0,
  limit: DEFAULT_PAGE_LIMIT,
  filter: [[]],
  order_by: [['id', 'DESC']],
});

export const useNotebookStore = create<{
  users: Record<string, UserNotebookData>;
  loading: boolean;
  setCurrentType: (type: NotebookType) => Promise<void>;
  fetchEntries: () => Promise<void>;
  applyPagination: (offset: number, limit: number) => void;
  setFilter: (filter: Filter | null) => void;
  addEntries: (entries: Entry[]) => Promise<void>;
  updateEntry: (ids: string[], values: Entry) => Promise<void>;
  deleteEntries: (ids: string[]) => Promise<void>;
}>((set, get) => ({
  users: {},
  loading: false,

  setCurrentType: async (type: NotebookType) => {
    const userName = getCurrentUserName();
    if (!userName) {
      handleError(new Error('未选择用户'), '加载失败');
      return;
    }
    if (!get().users[userName]) {
      set(state => ({ users: { ...state.users, [userName]: defaultUserData() } }));
    }

    try {
      set(state => {
        const existing = state.users[userName];
        return {
          users: { ...state.users,
            [userName]: existing ? { ...existing, type, entries: [], schema: null, filter: [[]], loaded: false }
              : { ...defaultUserData(), type: type },
          },
          loading: true,
        };
      });

      const schema = await getCachedSchema(type);
      set(state => {
        const existing = state.users[userName];
        return {
          users: { ...state.users,
            [userName]: existing ? { ...existing, schema }
              : { ...defaultUserData(), schema, type: type },
          },
        };
      });
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
    if (!userData || !userData.type) return;
    const { type, offset, limit, filter, order_by, view } = userData;
    try {
      set({ loading: true });
      const queryParams: Parameters<typeof queryEntries>[1] = {
        view, offset, limit, order_by, filter
      };
      const res = await queryEntries(type, queryParams);
      set(state => {
        const existing = state.users[userName];
        return {
          users: {
            ...state.users,
            [userName]: existing
              ? {
                  ...existing,
                  entries: res.results,
                  total: res.count,
                  loaded: true,
                }
              : {
                  ...defaultUserData(),
                  entries: res.results,
                  total: res.count,
                  loaded: true,
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

  applyPagination: (offset: number, limit: number) => {
    const userName = getCurrentUserName();
    if (!userName) return;
    const userData = get().users[userName];
    if (!userData) return;
    set(state => {
      const existing = state.users[userName];
      return {
        users: {
          ...state.users,
          [userName]: existing ? { ...existing, offset, limit } : { ...defaultUserData(), offset, limit },
        },
      };
    });
    get().fetchEntries();
  },

  setFilter: (filter: Filter | null) => {
    const userName = getCurrentUserName();
    if (!userName) return;
    set(state => {
      const existing = state.users[userName];
      return {
        users: {
          ...state.users,
          [userName]: existing
            ? { ...existing, filter: filter ?? [[]] }
            : { ...defaultUserData(), filter: filter ?? [[]] },
        },
      };
    });
    get().fetchEntries();
  },

  addEntries: async (entries: Entry[]) => {
    const userName = getCurrentUserName();
    if (!userName) return;
    const userData = get().users[userName];
    if (!userData || !userData.type) return;
    try {
      await addEntries(userData.type, entries);
      await get().fetchEntries();
    } catch (e: unknown) {
      handleError(e, '添加失败');
      throw e;
    }
  },

  updateEntry: async (ids: string[], values: Entry) => {
    const userName = getCurrentUserName();
    if (!userName) return;
    const userData = get().users[userName];
    if (!userData || !userData.type) return;
    try {
      await updateEntries(userData.type, ids, values);
      await get().fetchEntries();
    } catch (e: unknown) {
      handleError(e, '更新失败');
      throw e;
    }
  },

  deleteEntries: async (ids: string[]) => {
    const userName = getCurrentUserName();
    if (!userName) return;
    const userData = get().users[userName];
    if (!userData || !userData.type) return;
    try {
      await deleteEntries(userData.type, ids);
      await get().fetchEntries();
    } catch (e: unknown) {
      handleError(e, '删除失败');
      throw e;
    }
  },
}));
// TODO 前端在权限被拒时根据 ops 返回值提示

export const useCurrentNotebookData = () => {
  const userName = useTokenStore(s => s.activeUserName);
  return useNotebookStore(s => (userName ? s.users[userName] : null));
};
