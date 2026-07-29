import { api } from '@/api/client';
import type { InitDbResponse, BackupDbResponse, ResetDbResponse, RestoreDbResponse, ListBackupsResponse } from '@/types/api';

export const initDb = async (): Promise<InitDbResponse> =>
  api.post<InitDbResponse>('/db/init');

export const backupDb = async (): Promise<BackupDbResponse> =>
  api.post<BackupDbResponse>('/db/backup');

export const resetDb = async (): Promise<ResetDbResponse> =>
  api.post<ResetDbResponse>('/db/reset');

export const restoreDb = async (backupPath: string): Promise<RestoreDbResponse> =>
  api.post<RestoreDbResponse>('/db/restore', { backup_path: backupPath });

export const listBackups = async (): Promise<ListBackupsResponse> =>
  api.get<ListBackupsResponse>('/db/backups');
