import { create } from 'zustand';
import type { ChatMessage } from '@/types/api';
import { chat } from '@/api/ai';

interface ChatState {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;

  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
  clearError: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  loading: false,
  error: null,

  sendMessage: async (content: string) => {
    const { messages } = get();
    const userMsg: ChatMessage = { role: 'user', content };

    set({
      messages: [...messages, userMsg],
      loading: true,
      error: null,
    });

    try {
      const currentMessages = [...get().messages];
      const res = await chat({
        messages: currentMessages.map((m) => ({ role: m.role, content: m.content })),
      });

      const lastMsg = res.messages?.[res.messages.length - 1];
      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: lastMsg?.content || '',
      };

      set((s) => ({ messages: [...s.messages, assistantMsg] }));
    } catch (e: any) {
      set({ error: e.message || '对话失败' });
    } finally {
      set({ loading: false });
    }
  },

  clearMessages: () => set({ messages: [], error: null }),

  clearError: () => set({ error: null }),
}));
