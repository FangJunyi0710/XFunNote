export interface Token {
  id: string;
  name: string;
  token: string;
  permission: string;
  is_active: number;
  expires_at: string | null;
  shortcut: string | null;
  shortcut_expire_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TokenCreateRequest {
  name: string;
  permission: string;
  shortcut?: string;
  shortcut_ttl?: number;
}

export interface TokenUpdateRequest {
  name?: string;
  permission?: string;
  is_active?: boolean;
  expires_at?: string | null;
}

export interface ShortcutExchangeRequest {
  shortcut: string;
}

export interface ShortcutExchangeResponse {
  token: string;
}
