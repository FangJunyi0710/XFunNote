import { create } from 'zustand';
import type { ChatMessage } from '@/types/api';
import { chatStream } from '@/api/ai';

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
      const res = await chatStream({ message: content });

      if (!res.ok) {
        let detail = `HTTP ${res.status}`;
        try {
          const body = await res.json();
          detail = body.detail || detail;
        } catch {}
        throw new Error(detail);
      }

      const reader = res.body?.getReader();
      if (!reader) throw new Error('无响应流');

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: '',
        thinking: '',
      };

      // 将助手消息加入列表，后续修改
      set((s) => ({ messages: [...s.messages, assistantMsg] }));

      const decoder = new TextDecoder();
      let inThinking = false;
      let thinkingDone = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        // SSE 格式: "data: {...}\n\n"
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr) continue;

          try {
            const data = JSON.parse(jsonStr);

            if (data.type === 'token') {
              const token: string = data.content || '';
              // 检测 thinking 边界
              if (token === '[...thinking...]') {
                inThinking = true;
                continue;
              }
              if (token === '[.../thinking]') {
                inThinking = false;
                thinkingDone = true;
                continue;
              }

              set((s) => {
                const msgs = [...s.messages];
                const last = msgs[msgs.length - 1];
                if (last && last.role === 'assistant') {
                  if (inThinking || !thinkingDone) {
                    last.thinking = (last.thinking || '') + token;
                  } else {
                    last.content = (last.content || '') + token;
                  }
                }
                return { messages: msgs };
              });
            }
          } catch {
            // 跳过解析失败的块
          }
        }
      }
    } catch (e: any) {
      set({ error: e.message || '对话失败' });
    } finally {
      set({ loading: false });
    }
  },

  clearMessages: () => set({ messages: [], error: null }),

  clearError: () => set({ error: null }),
}));
