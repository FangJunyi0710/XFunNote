import { NotebookPlan } from '@/pages/NotebookPlan';
import { NotebookDiary } from '@/pages/NotebookDiary';
import { NotebookWord } from '@/pages/NotebookWord';
import { NotebookAccumulation } from '@/pages/NotebookAccumulation';
import { NotebookAimemory } from '@/pages/NotebookAimemory';
import { NotebookTimeline } from '@/pages/NotebookTimeline';
import { NotebookSchedule } from '@/pages/NotebookSchedule';

// ============================================================
// 笔记本类型配置 — 单一数据源 (SSOT)
// 所有样式、标签、颜色均由此派生，禁止在各组件中重复定义。
// ============================================================

/** 笔记本类型标识 */
export type NotebookType = 'plan' | 'diary' | 'word' | 'accumulation' | 'aimemory' | 'timeline' | 'schedule';

/** 所有笔记本类型的列表 */
export const NOTEBOOK_TYPES: NotebookType[] = [
  'plan',
  'diary',
  'word',
  'accumulation',
  'aimemory',
  'timeline',
  'schedule',
];

/** 中文标签映射 */
export const TYPE_LABELS: Record<NotebookType, string> = {
  plan: '计划',
  diary: '日记',
  word: '单词',
  accumulation: '积累',
  aimemory: 'AI 记忆',
  timeline: '时间线',
  schedule: '日程',
};

/** 元信息：标签 + 描述 */
export const NOTEBOOK_INFO: Record<string, { label: string; description: string }> = {
  plan: { label: '计划', description: '管理月度计划与任务' },
  diary: { label: '日记', description: '记录每日生活与感悟' },
  word: { label: '单词', description: '单词学习与复习' },
  accumulation: { label: '积累', description: '知识碎片整理与沉淀' },
  aimemory: { label: 'AI 记忆', description: 'AI 自动记录的关键信息' },
  timeline: { label: '时间线', description: '记录实际时间花费' },
  schedule: { label: '日程', description: '规划未来日程' },
};

/** 默认 Emoji 映射 */
export const DEFAULT_EMOJIS: Record<NotebookType, string> = {
  plan: '📋',
  diary: '📝',
  word: '📖',
  accumulation: '📚',
  aimemory: '🧠',
  timeline: '⏳',
  schedule: '📅',
};

// -------------------------------------------------------
// 颜色映射（用于样式工厂函数，也可直接使用）
// -------------------------------------------------------

/** 左侧边框颜色类名 */
const TYPE_COLORS: Record<NotebookType, string> = {
  plan: 'border-l-notebook-plan',
  diary: 'border-l-notebook-diary',
  word: 'border-l-notebook-word',
  accumulation: 'border-l-notebook-accumulation',
  aimemory: 'border-l-notebook-aimemory',
  timeline: 'border-l-notebook-timeline',
  schedule: 'border-l-notebook-schedule',
};

/** 聚焦环颜色类名 */
const TYPE_RING_COLORS: Record<NotebookType, string> = {
  plan: 'ring-notebook-plan',
  diary: 'ring-notebook-diary',
  word: 'ring-notebook-word',
  accumulation: 'ring-notebook-accumulation',
  aimemory: 'ring-notebook-aimemory',
  timeline: 'ring-notebook-timeline',
  schedule: 'ring-notebook-schedule',
};

/** 背景色类名 */
const TYPE_BG_COLORS: Record<NotebookType, string> = {
  plan: 'bg-notebook-plan/10',
  diary: 'bg-notebook-diary/10',
  word: 'bg-notebook-word/10',
  accumulation: 'bg-notebook-accumulation/10',
  aimemory: 'bg-notebook-aimemory/10',
  timeline: 'bg-notebook-timeline/10',
  schedule: 'bg-notebook-schedule/10',
};

/** 文字颜色类名 */
const TYPE_TEXT_COLORS: Record<NotebookType, string> = {
  plan: 'text-notebook-plan',
  diary: 'text-notebook-diary',
  word: 'text-notebook-word',
  accumulation: 'text-notebook-accumulation',
  aimemory: 'text-notebook-aimemory',
  timeline: 'text-notebook-timeline',
  schedule: 'text-notebook-schedule',
};

/** 颜色名称映射（用于 UI 中的颜色选择器等） */
export const NOTEBOOK_COLOR_NAMES: Record<NotebookType, string> = {
  plan: 'plan',
  diary: 'diary',
  word: 'word',
  accumulation: 'accumulation',
  aimemory: 'aimemory',
  timeline: 'timeline',
  schedule: 'schedule',
};

// -------------------------------------------------------
// 工厂函数：根据笔记本类型返回样式类名字典
// -------------------------------------------------------

export interface NotebookStyles {
  border: string;
  ring: string;
  bg: string;
  text: string;
}

/**
 * 根据笔记本类型获取所有样式类名。
 * 各组件通过此工厂函数派生样式，无需再自行维护颜色映射。
 */
export function getNotebookStyles(type: NotebookType): NotebookStyles {
  return {
    border: TYPE_COLORS[type] || '',
    ring: TYPE_RING_COLORS[type] || '',
    bg: TYPE_BG_COLORS[type] || '',
    text: TYPE_TEXT_COLORS[type] || '',
  };
}

/** 获取底部边框颜色（用于首页概览卡片） */
export function getNotebookBottomBorder(type: NotebookType): string {
  return TYPE_BORDER_BOTTOM_COLORS[type] || '';
}

// -------------------------------------------------------
// 向下兼容导出（旧代码可直接替换 import 来源）
// -------------------------------------------------------
// -------------------------------------------------------
// 路由配置
// -------------------------------------------------------
export const NOTEBOOK_ROUTES: Record<string, { path: string; icon: string; label: string }> = {
  plan: { path: '/notebooks/plan', icon: '📋', label: '计划' },
  diary: { path: '/notebooks/diary', icon: '📝', label: '日记' },
  word: { path: '/notebooks/word', icon: '📖', label: '单词' },
  accumulation: { path: '/notebooks/accumulation', icon: '📚', label: '积累' },
  aimemory: { path: '/notebooks/aimemory', icon: '🧠', label: 'AI 记忆' },
  timeline: { path: '/notebooks/timeline', icon: '⏳', label: '时间线' },
  schedule: { path: '/notebooks/schedule', icon: '📅', label: '日程' },
};

export { TYPE_COLORS, TYPE_RING_COLORS, TYPE_BG_COLORS, TYPE_TEXT_COLORS };

// -------------------------------------------------------
// 条目类型定义（各笔记本扩展字段）
// -------------------------------------------------------

// 通用条目核心字段（对应后端 BASE_COLUMNS）
export interface EntryBase {
  id: string;
  content: string;
  tags: string | null;
  note: string | null;
  is_ai_gen: number;
  ai_tags: string | null;
  ai_note: string | null;
  created_at: string;
  updated_at: string;
}

// Plan 笔记本扩展字段（对应 plan.py _extra_columns）
export interface PlanEntry extends EntryBase {
  no: string;
  seq: number;
  month: string;
  done: boolean | number;
}

// Diary 笔记本扩展字段（对应 diary.py _extra_columns）
export interface DiaryEntry extends EntryBase {
  date: string;
  mood: string | null;
  weather: string | null;
}

// Word 笔记本扩展字段（对应 word.py _extra_columns）
export interface WordEntry extends EntryBase {
  word: string;
  part_of_speech: string | null;
  phonetic: string | null;
  example: string | null;
  review_count: number;
  performance: number;
  next_review: string | null;
  last_review: string | null;
  related_words: string | null;
}

// Accumulation 笔记本扩展字段（对应 accumulation.py _extra_columns）
export interface AccumulationEntry extends EntryBase {
  source: string;
}

// AI Memory 笔记本扩展字段（对应 aimemory.py _extra_columns）
export interface AimemoryEntry extends EntryBase {
  title: string;
  source: string;
}

// Timeline 笔记本扩展字段
export interface TimelineEntry extends EntryBase {
  start_time: string;
  end_time?: string;
  location?: string;
  duration?: string;
}

// Schedule 笔记本扩展字段
export interface ScheduleEntry extends EntryBase {
  start_time: string;
  end_time?: string;
  location?: string;
  done: boolean | number;
}

// 条目联合类型
export type AnyEntry = PlanEntry | DiaryEntry | WordEntry | AccumulationEntry | AimemoryEntry | TimelineEntry | ScheduleEntry;

// -------------------------------------------------------
// 页面组件映射（用于路由动态渲染）
// -------------------------------------------------------

export type NotebookPageComponent = React.FC;

export const NOTEBOOK_PAGES: Record<NotebookType, NotebookPageComponent> = {
  plan: NotebookPlan,
  diary: NotebookDiary,
  word: NotebookWord,
  accumulation: NotebookAccumulation,
  aimemory: NotebookAimemory,
  timeline: NotebookTimeline,
  schedule: NotebookSchedule,
};
