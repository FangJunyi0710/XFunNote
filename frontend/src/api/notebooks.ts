import { api } from './client';
import type {
  NotebookSchema,
  QueryResponse,
  AddRequest,
  UpdateRequest,
  DeletePreview,
  DeleteResponse,
  NotebookType,
} from '@/types/notebook';

const NOTEBOOK_MAP: Record<NotebookType, string> = {
  plan: 'plan',
  diary: 'diary',
  word: 'word',
  accumulation: 'accumulation',
  aimemory: 'aimemory',
};

export async function listNotebooks(): Promise<NotebookSchema[]> {
  return api.get<NotebookSchema[]>('/notebooks');
}

export async function getSchema(type: NotebookType): Promise<NotebookSchema> {
  return api.get<NotebookSchema>(`/notebooks/${NOTEBOOK_MAP[type]}/schema`);
}

export async function queryEntries(
  type: NotebookType,
  params?: {
    filter?: string;
    page?: number;
    page_size?: number;
    order_by?: string;
    order_dir?: string;
  },
): Promise<QueryResponse> {
  const queryParams: Record<string, string> = {};
  if (params?.filter) queryParams.filter = params.filter;
  if (params?.page !== undefined) queryParams.page = String(params.page);
  if (params?.page_size !== undefined) queryParams.page_size = String(params.page_size);
  if (params?.order_by) queryParams.order_by = params.order_by;
  if (params?.order_dir) queryParams.order_dir = params.order_dir;
  return api.get<QueryResponse>(`/notebooks/${NOTEBOOK_MAP[type]}/entries`, queryParams);
}

export async function addEntries(
  type: NotebookType,
  data: AddRequest,
): Promise<{ message: string; ids: string[] }> {
  return api.post(`/notebooks/${NOTEBOOK_MAP[type]}/entries`, data);
}

export async function updateEntry(
  type: NotebookType,
  data: UpdateRequest,
): Promise<{ message: string }> {
  return api.put(`/notebooks/${NOTEBOOK_MAP[type]}/entries`, data);
}

export async function previewDelete(
  type: NotebookType,
  ids: string[],
): Promise<DeletePreview[]> {
  return api.post<DeletePreview[]>(
    `/notebooks/${NOTEBOOK_MAP[type]}/entries/delete-preview`,
    { ids },
  );
}

export async function deleteEntries(
  type: NotebookType,
  ids: string[],
): Promise<DeleteResponse> {
  return api.delete<DeleteResponse>(
    `/notebooks/${NOTEBOOK_MAP[type]}/entries`,
    { ids: ids.join(',') } as any,
  );
}

// Hack: need to send body in DELETE
export async function deleteEntriesWithBody(
  type: NotebookType,
  ids: string[],
): Promise<DeleteResponse> {
  const res = await fetch(
    `${window.location.origin}/api/v1/notebooks/${NOTEBOOK_MAP[type]}/entries`,
    {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids }),
    },
  );
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}
