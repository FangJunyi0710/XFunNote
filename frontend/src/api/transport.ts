// API 传输抽象：同一套调用，两种落地方式。
// - httpTransport：浏览器 / 远程（fetch 走 HTTP）
// - bridgeTransport：Android 本地模式（JS↔Kotlin 桥进程内直调 ApiService，无 HTTP）
// 两者返回同样的 {status, body}，因此上层 client.ts 与所有页面组件无需感知差异。

export interface ApiRequest {
  method: string;                   // GET / POST / PUT / DELETE
  path: string;                     // 含前缀，如 "/api/v0/tables/plan/entries"
  query: Record<string, string>;    // 已解码的查询参数（值可为 JSON 字符串）
  token: string | null;             // Bearer token
  user: string | null;              // 用户名（决定操作哪个库）
  body?: unknown;                   // 请求体（对象）
}

export interface RawResponse {
  status: number;
  body?: string;                    // JSON 字符串；无内容时省略该键
}

export type Transport = (req: ApiRequest) => Promise<RawResponse>;

// ---- Android 注入的桥对象类型 ----
declare global {
  interface Window {
    XFunBridge?: {
      /** 同步处理一次请求，返回 JSON 字符串形式的 {status, body}。 */
      request(reqJson: string): string;
    };
  }
}

// ---- HTTP 传输（默认 / 浏览器 / 远程） ----
export const httpTransport: Transport = async (req) => {
  const url = new URL(req.path, window.location.origin);
  for (const [k, v] of Object.entries(req.query)) {
    if (v !== undefined && v !== null) url.searchParams.set(k, v);
  }
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (req.token) headers['Authorization'] = `Bearer ${req.token}`;
  if (req.user) headers['User'] = req.user;

  const init: RequestInit = { method: req.method, headers };
  if (req.body !== undefined) init.body = JSON.stringify(req.body);

  const res = await fetch(url.toString(), init);
  const text = await res.text();
  return text ? { status: res.status, body: text } : { status: res.status };
};

// ---- JS 桥传输（Android 本地） ----
export const bridgeTransport: Transport = async (req) => {
  const bridge = window.XFunBridge;
  if (!bridge) throw new Error('XFunBridge 未注入');
  const out = bridge.request(JSON.stringify(req));   // 同步返回 {status, body} 的 JSON 字符串
  return JSON.parse(out) as RawResponse;
};

// 存在桥就用桥，否则用 HTTP（对现有 web 部署零影响）
export function detectTransport(): Transport {
  return typeof window !== 'undefined' && window.XFunBridge ? bridgeTransport : httpTransport;
}
