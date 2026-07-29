import { api } from '@/api/client';
import type { Permission, PermissionCreateRequest, PermissionUpdateRequest } from '@/types/permission';

export const listPermissions = async (): Promise<Permission[]> =>
  api.get<Permission[]>('/permissions');

export const getPermission = async (id: string): Promise<Permission> =>
  api.get<Permission>(`/permissions/${id}`);

export const createPermission = async (data: PermissionCreateRequest): Promise<Permission> =>
  api.post<Permission>('/permissions', data);

export const updatePermission = async (id: string, data: PermissionUpdateRequest): Promise<Permission> =>
  api.put<Permission>(`/permissions/${id}`, data);

export const deletePermission = async (id: string): Promise<void> =>
  api.delete<void>(`/permissions/${id}`);
