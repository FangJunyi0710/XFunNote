import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const generateId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;

export interface LocalTokenEntry {
  id: string;
  key: string;
  createdAt: string;
}

interface TokenStoreState {
  tokens: LocalTokenEntry[];
  activeTokenId: string | null;
  addToken: (key: string) => string | null;
  removeToken: (id: string) => void;
  setActiveToken: (id: string | null) => void;
  updateTokenKey: (id: string, key: string) => void;
  getActiveTokenKey: () => string | null;
}

export const useTokenStore = create<TokenStoreState>()(
  persist(
    (set, get) => ({
      tokens: [],
      activeTokenId: null,

      addToken: (key: string) => {
        const id = generateId();
        let added = false;
        set((state) => {
          // 检查是否已存在相同的 key
          if (state.tokens.some((t) => t.key === key)) {
            return state; // 已存在，不重复添加
          }
          added = true;
          return {
            tokens: [
              ...state.tokens,
              { id, key, createdAt: new Date().toISOString() },
            ],
          };
        });
        return added ? id : null;
      },

      removeToken: (id: string) => {
        set((state) => ({
          tokens: state.tokens.filter((t) => t.id !== id),
          activeTokenId: state.activeTokenId === id ? null : state.activeTokenId,
        }));
      },

      setActiveToken: (id: string | null) => {
        set({ activeTokenId: id });
      },

      updateTokenKey: (id: string, key: string) => {
        set((state) => ({
          tokens: state.tokens.map((t) =>
            t.id === id ? { ...t, key } : t,
          ),
        }));
      },

      getActiveTokenKey: () => {
        const { tokens, activeTokenId } = get();
        if (!activeTokenId) return null;
        const active = tokens.find((t) => t.id === activeTokenId);
        return active ? active.key : null;
      },
    }),
    {
      name: 'xfun-token-storage',
    },
  ),
);
