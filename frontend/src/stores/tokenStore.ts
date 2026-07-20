import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const generateId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;

export interface LocalTokenEntry {
  id: string;
  key: string;
  createdAt: string;
}

interface UserData {
  tokens: LocalTokenEntry[];
  activeTokenId: string | null;
}

interface TokenStoreState {
  users: Record<string, UserData>;
  activeUserName: string | null;
  addUser: (userName: string) => void;
  removeUser: (userName: string) => void;
  setActiveUser: (userName: string | null) => void;
  getCurrentUserTokens: () => LocalTokenEntry[];
  getActiveTokenKey: () => string | null;
  addToken: (key: string) => string | null;
  removeToken: (id: string) => void;
  setActiveToken: (id: string | null) => void;
  updateTokenKey: (id: string, key: string) => void;
}

const defaultUserData = (): UserData => ({
  tokens: [],
  activeTokenId: null,
});

export const useTokenStore = create<TokenStoreState>()(
  persist(
    (set, get) => ({
      users: {},
      activeUserName: null,

      addUser: (userName: string) => {
        set((state) => {
          if (state.users[userName]) return state;
          return {
            users: {
              ...state.users,
              [userName]: defaultUserData(),
            },
          };
        });
      },

      removeUser: (userName: string) => {
        set((state) => {
          const { [userName]: _, ...rest } = state.users;
          return {
            users: rest,
            activeUserName: state.activeUserName === userName ? null : state.activeUserName,
          };
        });
      },

      setActiveUser: (userName: string | null) => {
        set({ activeUserName: userName });
      },

      getCurrentUserTokens: () => {
        const { users, activeUserName } = get();
        if (!activeUserName || !users[activeUserName]) return [];
        return users[activeUserName].tokens;
      },

      getActiveTokenKey: () => {
        const { users, activeUserName } = get();
        if (!activeUserName || !users[activeUserName]) return null;
        const user = users[activeUserName];
        if (!user.activeTokenId) return null;
        const active = user.tokens.find((t) => t.id === user.activeTokenId);
        return active ? active.key : null;
      },

      addToken: (key: string) => {
        const { users, activeUserName } = get();
        if (!activeUserName || !users[activeUserName]) return null;
        const id = generateId();
        let added = false;
        set((state) => {
          const user = state.users[activeUserName];
          if (user.tokens.some((t) => t.key === key)) {
            return state;
          }
          added = true;
          return {
            users: {
              ...state.users,
              [activeUserName]: {
                ...user,
                tokens: [
                  ...user.tokens,
                  { id, key, createdAt: new Date().toISOString() },
                ],
              },
            },
          };
        });
        return added ? id : null;
      },

      removeToken: (id: string) => {
        const { users, activeUserName } = get();
        if (!activeUserName || !users[activeUserName]) return;
        set((state) => {
          const user = state.users[activeUserName];
          return {
            users: {
              ...state.users,
              [activeUserName]: {
                ...user,
                tokens: user.tokens.filter((t) => t.id !== id),
                activeTokenId: user.activeTokenId === id ? null : user.activeTokenId,
              },
            },
          };
        });
      },

      setActiveToken: (id: string | null) => {
        const { users, activeUserName } = get();
        if (!activeUserName || !users[activeUserName]) return;
        set((state) => ({
          users: {
            ...state.users,
            [activeUserName]: {
              ...state.users[activeUserName],
              activeTokenId: id,
            },
          },
        }));
      },

      updateTokenKey: (id: string, key: string) => {
        const { users, activeUserName } = get();
        if (!activeUserName || !users[activeUserName]) return;
        set((state) => {
          const user = state.users[activeUserName];
          return {
            users: {
              ...state.users,
              [activeUserName]: {
                ...user,
                tokens: user.tokens.map((t) =>
                  t.id === id ? { ...t, key } : t
                ),
              },
            },
          };
        });
      },
    }),
    {
      name: 'xfun-token-storage',
    }
  )
);
