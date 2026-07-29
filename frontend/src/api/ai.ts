import { api } from '@/api/client';
import type { ChatRequest, ChatResponse } from '@/types/api';

export const chat = async (data: ChatRequest): Promise<ChatResponse> =>
    api.post<ChatResponse>('/ai/chat', data);
