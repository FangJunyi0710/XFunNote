import { NotebookPlan } from '@/pages/NotebookPlan';
import { NotebookDiary } from '@/pages/NotebookDiary';
import { NotebookWord } from '@/pages/NotebookWord';
import { NotebookAccumulation } from '@/pages/NotebookAccumulation';
import { NotebookAimemory } from '@/pages/NotebookAimemory';
import { NotebookTimeline } from '@/pages/NotebookTimeline';
import { NotebookSchedule } from '@/pages/NotebookSchedule';
import { NotebookLedger } from '@/pages/NotebookLedger';

// ============================================================
// 笔记本类型配置 — 单一数据源 (SSOT)
// 所有样式、标签、颜色均由此派生，禁止在各组件中重复定义。
// ============================================================

/** 笔记本类型标识 */
export type NotebookType = 'plan' | 'diary' | 'word' | 'accumulation' | 'aimemory' | 'timeline' | 'schedule' | 'ledger';

/** 所有笔记本类型的列表 */
export const NOTEBOOK_TYPES: NotebookType[] = [
  'plan',
  'diary',
  'word',
  'accumulation',
  'aimemory',
  'timeline',
  'schedule',
  'ledger',
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
  ledger: '账本',
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
  ledger: { label: '账本', description: '记录收支流水' },
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
  ledger: 'border-l-notebook-ledger',
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
  ledger: 'ring-notebook-ledger',
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
  ledger: 'bg-notebook-ledger/10',
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
  ledger: 'text-notebook-ledger',
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
  ledger: 'ledger',
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

// -------------------------------------------------------
// 向下兼容导出（旧代码可直接替换 import 来源）
// -------------------------------------------------------
// -------------------------------------------------------
// 路由配置
// -------------------------------------------------------
export const NOTEBOOK_ROUTES: Record<string, { path: string; label: string }> = {
  plan: { path: '/notebooks/plan', label: '计划' },
  diary: { path: '/notebooks/diary', label: '日记' },
  word: { path: '/notebooks/word', label: '单词' },
  accumulation: { path: '/notebooks/accumulation', label: '积累' },
  aimemory: { path: '/notebooks/aimemory', label: 'AI 记忆' },
  timeline: { path: '/notebooks/timeline', label: '时间线' },
  schedule: { path: '/notebooks/schedule', label: '日程' },
  ledger: { path: '/notebooks/ledger', label: '账本' },
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
  stability: number;
  difficulty: number;
  state: number;
  lapses: number;
  step: number;
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
}

// Ledger 笔记本扩展字段（对应 ledger.py _extra_columns）
export interface LedgerEntry extends EntryBase {
  date: string;
  amount_cents: number;
  account: string | null;
}

// Schedule 笔记本扩展字段
export interface ScheduleEntry extends EntryBase {
  start_time: string;
  end_time?: string;
  location?: string;
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
  ledger: NotebookLedger,
};

// -------------------------------------------------------
// 列名 → 渲染器类型映射（用于表单字段特殊渲染）
// -------------------------------------------------------
export const COLUMN_RENDERER_TYPES: Record<string, string> = {
  content: 'Textarea',
  done: 'Boolean',
  is_ai_gen: 'Boolean',
  date: 'Date',
  created_at: 'DateTime',
  updated_at: 'DateTime',
  expires_at: 'DateTime',
  shortcut_expires_at: 'DateTime',
  start_time: 'DateTime',
  end_time: 'DateTime',
  next_review: 'DateTime',
  last_review: 'DateTime',
  state: 'Select',
};

// ── 字段名 ↔ 显示标签 双向映射 ───────────────────────────────

export const FIELD_LABEL_MAP: Record<string, string> = {
  // 通用字段 (BASE_COLUMNS)
  id: 'ID',
  content: '内容',
  created_at: '创建时间',
  updated_at: '更新时间',
  tags: '标签',
  note: '备注',
  is_ai_gen: 'AI 生成',
  ai_tags: 'AI 标签',
  ai_note: 'AI 备注',

  // Plan 笔记本特有
  no: '编号',
  seq: '序号',
  month: '月份',
  done: '完成情况',

  // Diary 笔记本特有
  date: '日期',
  mood: '心情',
  weather: '天气',

  // Word 笔记本特有
  word: '单词',
  part_of_speech: '词性',
  phonetic: '音标',
  example: '例句',
  review_count: '复习次数',
  stability: '稳定度',
  difficulty: '难度',
  state: '状态',
  lapses: '遗忘次数',
  step: '学习步数',
  next_review: '下次复习',
  last_review: '上次复习',
  related_words: '相关词',

  // Accumulation 笔记本特有
  source: '来源',

  // Aimemory 笔记本特有
  title: '标题',

  // Timeline / Schedule 笔记本特有
  start_time: '开始时间',
  end_time: '结束时间',
  location: '地点',

  // Ledger 笔记本特有
  amount_cents: '金额',
  account: '账户',

  // 其他可能出现的字段
  expires_at: '过期时间',
  shortcut_expires_at: '快捷码过期时间',
};

export function getFieldLabel(fieldName: string): string {
  return FIELD_LABEL_MAP[fieldName] ?? fieldName;
}


// ── 字段值转换（存储 ↔ 显示） ───────────────────────────────

/** 创建枚举类型字段的转换器 */
function makeEnumTransform<T extends Record<string, string>>(options: T) {
  return {
    options,
    toDisplay: (v: unknown) => v === null || v === undefined ? '' : options[v as string] ?? String(v),
    toStorage: (v: unknown) => {
      if (v === '' || v === null || v === undefined) return null;
      const entry = Object.entries(options).find(([, display]) => display === v);
      if (entry) {
        const key = entry[0];
        return isNaN(Number(key)) ? key : Number(key);
      }
      const num = Number(v); 
      return isNaN(num) ? null : num;
    }
  };
}

export const FIELD_TRANSFORMS: Record<string, {
  toDisplay: (v: unknown) => unknown;
  toStorage: (v: unknown) => unknown;
  options?: Record<number | string, string>;
}> = {
  // 金额：分 ↔ 元，无枚举选项
  amount_cents: {
    toDisplay: (v) => v !== null && v !== undefined && v !== '' ? (Number(v) / 100).toFixed(2) : '',
    toStorage: (v) => {
      if (v === '' || v === null || v === undefined) return null;
      const num = parseFloat(String(v));
      return isNaN(num) ? null : Math.round(num * 100);
    },
  },
  // 枚举字段：仅需定义映射表
  done: makeEnumTransform({ 0: '未完成', 1: '已完成' }),
  is_ai_gen: makeEnumTransform({ 0: '否', 1: '是' }),
  state: makeEnumTransform({ 0: '全新', 1: '学习', 2: '复习', 3: '重学' }),
};

export const toDisplay = (field: string, v: unknown) =>
  FIELD_TRANSFORMS[field]?.toDisplay(v) ?? v;

export const toStorage = (field: string, v: unknown) =>
  FIELD_TRANSFORMS[field]?.toStorage(v) ?? v;
