import { api } from './client';
import type { InitDbResponse, BackupDbResponse, ResetDbResponse } from '@/types/api';

export async function initDb(): Promise<InitDbResponse> {
  return api.post<InitDbResponse>('/management/init');
}

export async function backupDb(): Promise<BackupDbResponse> {
  return api.post<BackupDbResponse>('/management/backup');
}

export async function resetDb(): Promise<ResetDbResponse> {
  return api.post<ResetDbResponse>('/management/reset');
}
