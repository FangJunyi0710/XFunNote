// 基础 HTTP 客户端

const BASE_URL = '/api/v1';

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
  if (res.status === 204) return undefined as unknown as T;
  return res.json();
}

async function request<T>(
  method: string,
  path: string,
  body?: any,
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

  // 如果配置了 VITE_API_KEY，则添加鉴权头
  const apiKey = import.meta.env.VITE_API_KEY;
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

  post: <T>(path: string, body?: any) => request<T>('POST', path, body),

  put: <T>(path: string, body?: any) => request<T>('PUT', path, body),

  delete: <T>(path: string, body?: any) => request<T>('DELETE', path, body),
};
