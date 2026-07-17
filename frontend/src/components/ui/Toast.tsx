import React, { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import { cn } from '@/lib/utils';

// ── 类型定义 ───────────────────────────────────────

interface ToastItem {
  id: string;
  message: string;
  type: 'error' | 'success';
  /** 用户点击后变为常驻 */
  pinned: boolean;
  /** 动画状态 */
  exiting: boolean;
}

type ToastListener = (toast: Omit<ToastItem, 'id' | 'pinned' | 'exiting'>) => void;

// ── 全局订阅模式 ────────────────────────────────────

let listener: ToastListener | null = null;

export function showToast(message: string, type: 'error' | 'success' = 'error') {
  listener?.({ message, type });
}

export const toast = {
  error: (msg: string) => showToast(msg, 'error'),
  success: (msg: string) => showToast(msg, 'success'),
};

// ── Toast 组件 ──────────────────────────────────────

// 自动消失时间（按类型区分）
const AUTO_DISMISS_MS = 1000
const DISMISS_ANIM_DURATION_MS = 300

export const ToastContainer: React.FC = () => {
  const [items, setItems] = useState<ToastItem[]>([]);
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  // 订阅全局通知
  useEffect(() => {
    listener = (t) => {
      const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
      const newItem: ToastItem = { ...t, id, pinned: false, exiting: false };
      setItems((prev) => [...prev, newItem]);
    };
    return () => { listener = null; };
  }, []);

  // 启动自动消失计时器
  const startTimer = useCallback((item: ToastItem) => {
    const ms = AUTO_DISMISS_MS;
    const timer = setTimeout(() => {
      // 进入退出动画
      setItems((prev) => prev.map((i) => i.id === item.id ? { ...i, exiting: true } : i));
      // 动画结束后移除
      setTimeout(() => {
        setItems((prev) => prev.filter((i) => i.id !== item.id));
        timersRef.current.delete(item.id);
      }, DISMISS_ANIM_DURATION_MS);
    }, ms);
    timersRef.current.set(item.id, timer);
  }, []);

  // 暂停计时器
  const clearTimer = useCallback((id: string) => {
    const timer = timersRef.current.get(id);
    if (timer) clearTimeout(timer);
    timersRef.current.delete(id);
  }, []);

  // 用户点击 — 变为不透明且不自动消失
  const handlePin = useCallback((id: string) => {
    setItems((prev) => prev.map((item) => item.id === id ? { ...item, pinned: true } : item));
    clearTimer(id);
  }, [clearTimer]);

  // 关闭
  const handleDismiss = useCallback((id: string) => {
    clearTimer(id);
    setItems((prev) => prev.map((item) => item.id === id ? { ...item, exiting: true } : item));
    setTimeout(() => {
      setItems((prev) => prev.filter((item) => item.id !== id));
    }, DISMISS_ANIM_DURATION_MS);
  }, [clearTimer]);

  // 新加入时启动计时器
  useEffect(() => {
    items.forEach((item) => {
      if (!item.pinned && !timersRef.current.has(item.id)) {
        startTimer(item);
      }
    });
  }, [items, startTimer]);

  if (items.length === 0) return null;

  return createPortal(
    <div className="fixed top-4 left-1/2 -translate-x-1/2 z-[9999] flex flex-col gap-2 pointer-events-none">
      {items.map((item) => (
        <div
          key={item.id}
          onClick={() => item.pinned ? handleDismiss(item.id) : handlePin(item.id)}
          className={cn(
            'pointer-events-auto flex items-center gap-2 px-4 py-3 rounded-lg border shadow-lg max-w-md cursor-pointer select-none',
            'transition-all duration-300',
            item.exiting ? 'opacity-0 -translate-y-2' : 'opacity-80',
            item.pinned && 'opacity-100',
            item.type === 'error'
              ? `${item.pinned ? 'bg-destructive border-destructive/30 text-destructive-foreground' : 'bg-destructive/15 border-destructive/30 text-destructive'}`
              : `${item.pinned ? 'bg-success border-success/30 text-success-foreground' : 'bg-success/15 border-success/30 text-success'}`,
          )}
        >
          <span className="text-sm flex-1 min-w-0">{item.message}</span>
        </div>
      ))}
    </div>,
    document.body,
  );
};
