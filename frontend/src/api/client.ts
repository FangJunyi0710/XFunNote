// 基础 HTTP 客户端
import pkg from '../../package.json';

const API_VERSION = pkg.version.split('.')[0];
const BASE_URL = `/api/v${API_VERSION}`;

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public errorCode?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || body.message || detail;
    } catch {
      // ignore parse error
    }
    throw new ApiError(res.status, detail);
  }
  // 204 No Content
  if (res.status === 204) return undefined as T;
  return res.json();
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  params?: Record<string, string>,
): Promise<T> {
  const url = new URL(`${BASE_URL}${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) url.searchParams.set(k, v);
    });
  }

  const options: RequestInit = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };

  // 从浏览器本地存储的 token 列表中获取当前使用的 token
  const { useTokenStore } = await import('@/stores/tokenStore');
  const apiKey = useTokenStore.getState().getActiveTokenKey();
  if (apiKey) {
    options.headers = { ...options.headers, 'X-API-Key': apiKey };
  }

  if (body !== undefined) {
    options.body = JSON.stringify(body);
  }

  const res = await fetch(url.toString(), options);
  return handleResponse<T>(res);
}

export const api = {
  get: <T>(path: string, params?: Record<string, string>) =>
    request<T>('GET', path, undefined, params),

  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),

  put: <T>(path: string, body?: unknown) => request<T>('PUT', path, body),

  delete: <T>(path: string, body?: unknown) => request<T>('DELETE', path, body),
};
