import { api } from './client';
import type { Permission, PermissionCreateRequest, PermissionUpdateRequest } from '@/types/permission';

export async function listPermissions(): Promise<Permission[]> {
  return api.get<Permission[]>('/permissions');
}

export async function getPermission(id: string): Promise<Permission> {
  return api.get<Permission>(`/permissions/${id}`);
}

export async function createPermission(data: PermissionCreateRequest): Promise<Permission> {
  return api.post<Permission>('/permissions', data);
}

export async function updatePermission(id: string, data: PermissionUpdateRequest): Promise<Permission> {
  return api.put<Permission>(`/permissions/${id}`, data);
}

export async function deletePermission(id: string): Promise<void> {
  return api.delete<void>(`/permissions/${id}`);
}
