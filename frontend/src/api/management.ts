import { api } from './client';
import type { InitDbResponse, BackupDbResponse, ResetDbResponse, RestoreDbResponse, ListBackupsResponse } from '@/types/api';

export async function initDb(): Promise<InitDbResponse> {
  return api.post<InitDbResponse>('/db/init');
}

export async function backupDb(): Promise<BackupDbResponse> {
  return api.post<BackupDbResponse>('/db/backup');
}

export async function resetDb(): Promise<ResetDbResponse> {
  return api.post<ResetDbResponse>('/db/reset');
}

export async function restoreDb(backupPath: string): Promise<RestoreDbResponse> {
  return api.post<RestoreDbResponse>('/db/restore', { backup_path: backupPath });
}

export async function listBackups(): Promise<ListBackupsResponse> {
  return api.get<ListBackupsResponse>('/db/backups');
}
