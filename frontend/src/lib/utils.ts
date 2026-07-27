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

/**
 * 获取当前时区偏移字符串，如 "+8"、"-5"、"+5:30"
 */
export function getTimezoneOffsetStr(): string {
  const offset = -new Date().getTimezoneOffset() / 60;
  if (Number.isInteger(offset)) {
    return (offset >= 0 ? '+' : '') + offset.toString();
  }
  const hours = Math.floor(offset);
  const minutes = Math.abs((offset - hours) * 60);
  return (hours >= 0 ? '+' : '') + hours + ':' + String(minutes).padStart(2, '0');
}

function generate64ColorPalette(): string[] {
  // 8 种感知差异最大的核心色相（跳过相近区间，均匀分布）
  const hues = [0, 25, 50, 160, 200, 260, 310, 340];
  // 8 种不同的“质感”：[饱和度%, 明度%]
  const variants: [number, number][] = [
    [90, 45], // 鲜艳深色
    [70, 65], // 柔和中性
    [50, 35], // 暗淡深色（高级灰）
    [85, 75], // 鲜艳浅色
    [60, 55], // 柔和中深
    [95, 70], // 极致鲜艳明亮
    [40, 50], // 低饱和中明度（莫兰迪）
    [80, 85], // 鲜艳极浅（粉蜡笔）
  ];
  const colors: string[] = [];
  for (const hue of hues) {
    for (const [sat, light] of variants) {
      colors.push(`hsl(${hue}, ${sat}%, ${light}%)`);
    }
  }
  return colors;
}

const PALETTE_64 = generate64ColorPalette();

export function getColorFromString(str: string): string {
  let hash = 0;
  for (const ch of str) {
    hash = (hash * 31 + ch.charCodeAt(0)) | 0;
  }
  return PALETTE_64[Math.abs(hash) % PALETTE_64.length]!;
}
