import { api } from './client';
import type { ChatRequest, ChatResponse, AIPermissionRequest } from '@/types/api';

export async function chat(data: ChatRequest): Promise<ChatResponse> {
  return api.post<ChatResponse>('/ai/chat', data);
}

/**
 * 流式 AI 对话
 * 返回 ReadableStream，由调用方逐块处理
 */
export function chatStream(data: ChatRequest): Promise<Response> {
  return fetch(`${window.location.origin}/api/v1/ai/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...data, stream: true }),
  });
}

/**
 * 查询 AI 当前权限（read_view / write_view）
 */
export async function getPermission(): Promise<{
  read_view: any;
  write_view: any;
}> {
  return api.get('/ai/permission');
}

/**
 * 设置 AI 权限
 */
export async function setPermission(data: AIPermissionRequest): Promise<{
  message: string;
}> {
  return api.post('/ai/permission', data);
}
