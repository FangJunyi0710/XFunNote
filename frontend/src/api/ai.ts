import { api } from './client';
import type { ChatRequest, ChatResponse } from '@/types/api';

export async function chat(data: ChatRequest): Promise<ChatResponse> {
  return api.post<ChatResponse>('/ai/chat', data);
}
