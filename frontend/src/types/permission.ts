export interface Permission {
  id: string;
  name: string;
  description: string | null;
  read_view: string;
  write_view: string;
  created_at: string;
  updated_at: string;
}

export interface PermissionCreateRequest {
  id: string;
  name: string;
  description?: string;
  read_view: Record<string, any>;
  write_view: Record<string, any>;
}

export interface PermissionUpdateRequest {
  name?: string;
  description?: string;
  read_view?: Record<string, any>;
  write_view?: Record<string, any>;
}
