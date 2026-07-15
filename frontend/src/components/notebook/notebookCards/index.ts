import React from 'react';
import type { NotebookType } from '@/config/notebook';

/** 卡片渲染器：给定 entry 返回 JSX 内容（渲染在 CardContent 内部） */
export type CardRenderer = React.FC<{ entry: Record<string, unknown> }>;

const registry = new Map<string, CardRenderer>();

export function registerCard(type: NotebookType, renderer: CardRenderer): void {
  registry.set(type, renderer);
}

export function getCardRenderer(type: string): CardRenderer | undefined {
  return registry.get(type);
}
