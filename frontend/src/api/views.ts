import { api } from './client';
import type { ViewFile, ViewData } from '@/types/view';

export async function listViews(): Promise<ViewFile[]> {
  return api.get<ViewFile[]>('/views');
}

export async function getView(name: string): Promise<ViewData> {
  return api.get<ViewData>(`/views/${name}`);
}

export async function saveView(name: string, data: ViewData): Promise<{ message: string }> {
  return api.put<{ message: string }>(`/views/${name}`, data);
}

export async function deleteView(name: string): Promise<{ message: string }> {
  return api.delete<{ message: string }>(`/views/${name}`);
}
