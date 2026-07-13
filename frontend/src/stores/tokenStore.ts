import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface LocalTokenEntry {
  id: string;
  key: string;
  createdAt: string;
}

interface TokenStoreState {
  tokens: LocalTokenEntry[];
  activeTokenId: string | null;
  addToken: (key: string) => void;
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
        const id = crypto.randomUUID();
        set((state) => ({
          tokens: [
            ...state.tokens,
            { id, key, createdAt: new Date().toISOString() },
          ],
        }));
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
