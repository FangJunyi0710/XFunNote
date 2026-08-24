import { api } from '@/api/client';

export interface TokenInfo {
  name: string;
  shortcut: string | null;
  shortcut_expire_at: string | null;
  expires_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  read_view: Record<string, unknown>;
  write_view: Record<string, unknown>;
  is_active: boolean;
}

interface ShortcutExchangeRequest {
  shortcut: string;
}

interface ShortcutExchangeResponse {
  token: string;
}

export const getTokenInfo = async (): Promise<TokenInfo> =>
  api.get<TokenInfo>('/tokens/info');

export const exchangeTokenByShortcut = async (data: ShortcutExchangeRequest): Promise<ShortcutExchangeResponse> =>
  api.post<ShortcutExchangeResponse>('/tokens/exchange', data);
