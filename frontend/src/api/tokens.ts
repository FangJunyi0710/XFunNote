import { api } from './client';
import type { Token, TokenCreateRequest, TokenUpdateRequest } from '@/types/token';

export async function listTokens(): Promise<Token[]> {
  return api.get<Token[]>('/tokens');
}

export async function getToken(id: string): Promise<Token> {
  return api.get<Token>(`/tokens/${id}`);
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
