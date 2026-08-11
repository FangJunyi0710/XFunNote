import { api } from '@/api/client';

export const chat = async (data: ChatRequest): Promise<ChatResponse> =>
    api.post<ChatResponse>('/ai/chat', data);
