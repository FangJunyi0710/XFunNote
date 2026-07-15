import { api } from './client';

export interface FilterFile {
  id: string;
  name: string;
  data: string;
  created_at: string;
  updated_at: string;
}

export async function listFilters(): Promise<FilterFile[]> {
  return api.get<FilterFile[]>('/filters');
}

export async function getFilter(name: string): Promise<any> {
  return api.get<any>(`/filters/${name}`);
}

export async function saveFilter(name: string, data: any): Promise<{ message: string }> {
  return api.put<{ message: string }>(`/filters/${name}`, data);
}

export async function deleteFilter(name: string): Promise<{ message: string }> {
  return api.delete<{ message: string }>(`/filters/${name}`);
}
