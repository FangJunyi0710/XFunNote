// 基础 API 客户端：只负责组装请求 + 处理响应，具体走 HTTP 还是 JS 桥由 transport 决定。
import pkg from '../../package.json';
import { useTokenStore } from '@/stores/tokenStore';
import { detectTransport, type ApiRequest, type RawResponse } from '@/api/transport';

const API_VERSION = pkg.version.split('.')[0];
const BASE_URL = `/api/v${API_VERSION}`;

const transport = detectTransport();

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

// 与原 handleResponse 逐分支等价：非 2xx 抛 ApiError(detail)，204 无内容，其余解析 JSON。
const handle = async <T>(raw: RawResponse): Promise<T> => {
  if (raw.status < 200 || raw.status >= 300) {
    let detail = `HTTP ${raw.status}`;
    try {
      const body = JSON.parse(raw.body || '{}');
      detail = body.detail || body.message || detail;
    } catch {
      // ignore parse error
    }
    throw new ApiError(raw.status, detail);
  }
  if (raw.status === 204 || !raw.body) return undefined as T;
  return JSON.parse(raw.body) as T;
};

const request = async <T>(
  method: string,
  path: string,
  body?: unknown,
  params?: Record<string, string>,
): Promise<T> => {
  // 从 store 获取当前用户和 Token
  const state = useTokenStore.getState();
  const userName = state.activeUserName;
  const token = state.getActiveToken();
  if (!userName) throw new Error('未设置用户名');

  const query: Record<string, string> = {};
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null) query[k] = v;
    }
  }

  const req: ApiRequest = {
    method,
    path: `${BASE_URL}${path}`,
    query,
    token,
    user: userName,
    body,
  };

  return handle<T>(await transport(req));
};

export const api = {
  get: <T>(path: string, params?: Record<string, string>) =>
    request<T>('GET', path, undefined, params),

  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),

  put: <T>(path: string, body?: unknown) => request<T>('PUT', path, body),

  delete: <T>(path: string, body?: unknown) => request<T>('DELETE', path, body),
};
