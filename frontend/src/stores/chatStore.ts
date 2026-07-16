import { create } from 'zustand';
import type { ChatMessage } from '@/types/api';
import { chat } from '@/api/ai';
import { handleError } from '@/lib/error';

interface ChatState {
  messages: ChatMessage[];
  loading: boolean;

  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  loading: false,

  sendMessage: async (content: string) => {
    const { messages } = get();
    const userMsg: ChatMessage = { role: 'user', content };

    set({
      messages: [...messages, userMsg],
      loading: true,
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
    } catch (e: unknown) {
      handleError(e, '对话失败');
    } finally {
      set({ loading: false });
    }
  },

  clearMessages: () => set({ messages: [] }),
}));
