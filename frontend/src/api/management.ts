import { api } from './client';
import type { InitDbResponse, BackupDbResponse, ResetDbResponse } from '@/types/api';

export async function initDb(): Promise<InitDbResponse> {
  return api.post<InitDbResponse>('/db/init');
}

export async function backupDb(): Promise<BackupDbResponse> {
  return api.post<BackupDbResponse>('/db/backup');
}

export async function resetDb(): Promise<ResetDbResponse> {
  return api.post<ResetDbResponse>('/db/reset');
}
