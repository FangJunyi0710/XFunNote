import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ChatMessage } from '@/types/api';
import { chat } from '@/api/ai';
import { handleError } from '@/lib/error';
import { useTokenStore } from './tokenStore';

interface UserChatData {
  messages: ChatMessage[];
}

interface ChatState {
  users: Record<string, UserChatData>;
  loading: boolean; // 全局加载状态，可按需保留，但也可按用户，但简单起见保留全局
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
}

const getCurrentUserName = () => useTokenStore.getState().activeUserName;

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      users: {},
      loading: false,

      sendMessage: async (content: string) => {
        const userName = getCurrentUserName();
        if (!userName) {
          handleError(new Error('未选择用户，请先切换用户'), '对话失败');
          return;
        }

        const userMessages = get().users[userName]?.messages || [];
        const userMsg: ChatMessage = { role: 'user', content };

        // 更新当前用户的 messages
        set((state) => ({
          users: {
            ...state.users,
            [userName]: {
              messages: [...userMessages, userMsg],
            },
          },
          loading: true,
        }));

        try {
          const currentMessages = get().users[userName]?.messages || [];
          const res = await chat({
            messages: currentMessages.map((m) => ({ role: m.role, content: m.content })),
          });

          const lastMsg = res.messages?.[res.messages.length - 1];
          const assistantMsg: ChatMessage = {
            role: 'assistant',
            content: lastMsg?.content || '',
          };

          set((state) => ({
            users: {
              ...state.users,
              [userName]: {
                messages: [...(state.users[userName]?.messages || []), assistantMsg],
              },
            },
          }));
        } catch (e: unknown) {
          handleError(e, '对话失败');
        } finally {
          set({ loading: false });
        }
      },

      clearMessages: () => {
        const userName = getCurrentUserName();
        if (!userName) return;
        set((state) => ({
          users: {
            ...state.users,
            [userName]: { messages: [] },
          },
        }));
      },
    }),
    {
      name: 'xfun-chat-storage',
      partialize: (state) => ({ users: state.users }), // 仅持久化 messages
    }
  )
);

// ── 自定义 hook：获取当前用户的数据 ──────────────────────────────

export const useCurrentChatData = () => {
  const userName = useTokenStore((s) => s.activeUserName);
  return useChatStore((s) => userName ? s.users[userName] : null);
};
