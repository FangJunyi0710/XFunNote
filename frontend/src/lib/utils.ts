import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

/**
 * 格式化日期为友好的显示格式
 */
export function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}

/**
 * 格式化日期时间为完整的日期+时间
 */
export function formatDateTime(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 生成唯一 ID
 */
export function genId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

/**
 * 对 Token 值进行脱敏显示（仅保留前6位）
 */
export function maskKey(key: string): string {
  if (!key) return '';
  if (key.length <= 6) return key;
  return key.slice(0, 6) + '...';
}

/**
 * 安全获取条目显示值，处理 undefined/null
 */
export function safeValue(obj: unknown, key: string, fallback = '-'): string {
  const v = (obj as Record<string, unknown>)?.[key];
  if (v === null || v === undefined || v === '') return fallback;
  return String(v);
}

/**
 * 校验用户名是否合法（与后端保持一致：^[a-zA-Z0-9\-_]{1,64}$）
 */
export function isValidUsername(username: string): boolean {
  if (!username) return false;
  const USERNAME_PATTERN = /^[a-zA-Z0-9\-_]{1,64}$/;
  return USERNAME_PATTERN.test(username);
}
