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

export const listTokens = async (): Promise<Token[]> =>
  api.get<Token[]>('/tokens');

export const getToken = async (id: string): Promise<Token> =>
  api.get<Token>(`/tokens/${id}`);

export const getTokenInfo = async (): Promise<TokenInfo> =>
  api.get<TokenInfo>('/tokens/info');

export const createToken = async (data: TokenCreateRequest): Promise<Token> =>
  api.post<Token>('/tokens', data);

export const updateToken = async (id: string, data: TokenUpdateRequest): Promise<Token> =>
  api.put<Token>(`/tokens/${id}`, data);

export const deleteToken = async (id: string): Promise<void> =>
  api.delete<void>(`/tokens/${id}`);

export const exchangeTokenByShortcut = async (data: ShortcutExchangeRequest): Promise<ShortcutExchangeResponse> =>
  api.post<ShortcutExchangeResponse>('/tokens/exchange', data);
