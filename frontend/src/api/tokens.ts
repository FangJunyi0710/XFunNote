import { api } from './client';
import type { Token, TokenCreateRequest, TokenUpdateRequest, ShortcutExchangeRequest, ShortcutExchangeResponse } from '@/types/token';

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

export async function listTokens(): Promise<Token[]> {
  return api.get<Token[]>('/tokens');
}

export async function getToken(id: string): Promise<Token> {
  return api.get<Token>(`/tokens/${id}`);
}

export async function getTokenInfo(): Promise<TokenInfo> {
  return api.get<TokenInfo>('/tokens/info');
}

export async function createToken(data: TokenCreateRequest): Promise<Token> {
  return api.post<Token>('/tokens', data);
}

export async function updateToken(id: string, data: TokenUpdateRequest): Promise<Token> {
  return api.put<Token>(`/tokens/${id}`, data);
}

export async function deleteToken(id: string): Promise<void> {
  return api.delete<void>(`/tokens/${id}`);
}

export async function exchangeTokenByShortcut(data: ShortcutExchangeRequest): Promise<ShortcutExchangeResponse> {
  return api.post<ShortcutExchangeResponse>('/tokens/exchange', data);
}
