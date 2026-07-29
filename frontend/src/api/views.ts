import { api } from '@/api/client';
import type { ViewFile, ViewData } from '@/types/view';

export const listViews = async (): Promise<ViewFile[]> =>
  api.get<ViewFile[]>('/views');

export const getView = async (name: string): Promise<ViewData> =>
  api.get<ViewData>(`/views/${name}`);

export const saveView = async (name: string, data: ViewData): Promise<{ message: string }> =>
  api.put<{ message: string }>(`/views/${name}`, data);

export const deleteView = async (name: string): Promise<{ message: string }> =>
  api.delete<{ message: string }>(`/views/${name}`);
