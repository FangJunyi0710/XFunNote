import { api } from '@/api/client';

export interface FilterFile {
  id: string;
  name: string;
  data: string;
  created_at: string;
  updated_at: string;
}

export type FilterData = Record<string, unknown>;

export const listFilters = async (): Promise<FilterFile[]> =>
  api.get<FilterFile[]>('/filters');

export const getFilter = async (name: string): Promise<FilterData> =>
  api.get<FilterData>(`/filters/${name}`);

export const saveFilter = async (name: string, data: FilterData): Promise<{ message: string }> =>
  api.put<{ message: string }>(`/filters/${name}`, data);

export const deleteFilter = async (name: string): Promise<{ message: string }> =>
  api.delete<{ message: string }>(`/filters/${name}`);
