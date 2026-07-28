import { NotebookPlan } from '@/pages/NotebookPlan';
import { NotebookDiary } from '@/pages/NotebookDiary';
import { NotebookWord } from '@/pages/NotebookWord';
import { NotebookAccumulation } from '@/pages/NotebookAccumulation';
import { NotebookAimemory } from '@/pages/NotebookAimemory';
import { NotebookTimeline } from '@/pages/NotebookTimeline';
import { NotebookSchedule } from '@/pages/NotebookSchedule';
import { NotebookLedger } from '@/pages/NotebookLedger';
import { getMajorityMonthForWeek } from '@/lib/utils';

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
  transaction_id: string;
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
export const COLUMN_TYPES: Record<string, string> = {
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

export const FIELD_LABEL_MAP: Record<string, { label: string; priority: number }> = {
  // 通用字段 (BASE_COLUMNS)
  content: { label: '内容', priority: 100 },
  note: { label: '备注', priority: 11 },
  tags: { label: '标签', priority: 10 },

  id: { label: 'ID', priority: 1000 },
  created_at: { label: '创建时间', priority: 910 },
  updated_at: { label: '更新时间', priority: 900 },
  is_ai_gen: { label: 'AI 生成', priority: 3 },
  ai_note: { label: 'AI 备注', priority: 2 },
  ai_tags: { label: 'AI 标签', priority: 1 },

  // Plan 笔记本特有
  month: { label: '月份', priority: 110 },
  done: { label: '完成情况', priority: 50 },

  no: { label: '编号', priority: 100 },
  seq: { label: '序号', priority: 80 },

  // Diary 笔记本特有
  date: { label: '日期', priority: 150 },
  weather: { label: '天气', priority: 90 },
  mood: { label: '心情', priority: 80 },

  // Word 笔记本特有
  word: { label: '单词', priority: 150 },
  phonetic: { label: '音标', priority: 140 },
  part_of_speech: { label: '词性', priority: 130 },
  example: { label: '例句', priority: 90 },
  related_words: { label: '相关词', priority: 80 },

  state: { label: '状态', priority: 500 },
  next_review: { label: '下次复习', priority: 490 },
  last_review: { label: '上次复习', priority: 480 },
  difficulty: { label: '难度', priority: 410 },
  stability: { label: '稳定度', priority: 400 },
  review_count: { label: '复习次数', priority: 310 },
  lapses: { label: '遗忘次数', priority: 300 },
  step: { label: '学习步数', priority: 90 },

  // Accumulation 笔记本特有
  source: { label: '来源', priority: 90 },

  // Aimemory 笔记本特有
  title: { label: '标题', priority: 150 },

  // Timeline / Schedule 笔记本特有
  start_time: { label: '开始时间', priority: 150 },
  end_time: { label: '结束时间', priority: 140 },
  location: { label: '地点', priority: 90 },

  // Ledger 笔记本特有
  transaction_id: { label: '交易ID', priority: 130 },
  account: { label: '账户', priority: 120 },
  amount_cents: { label: '金额', priority: 110 },
};

export function getFieldLabel(fieldName: string): string {
  return FIELD_LABEL_MAP[fieldName]?.label ?? fieldName;
}

export function getFieldPriority(fieldName: string): number {
  const entry = FIELD_LABEL_MAP[fieldName];
  return entry?.priority ?? -1;
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

const dateToDisplay = (val: unknown): string => {
  return datetimeToDisplay(val).split('T')[0] ?? '';
}

const datetimeToDisplay = (val: unknown): string => {
  const d = typeof val === 'string' ? new Date(val) : val;
  if (d instanceof Date && !isNaN(d.getTime())) {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  }
  return '';
};

const datetimeToStorage = (val: unknown): string | null => {
  if(typeof val !== 'string') {
    return null;
  }
  const d = new Date(val);
  if (!isNaN(d.getTime())) {
    return d.toISOString();
  }
  return null;
}

export const FIELD_TRANSFORMS: Record<string, {
  toDisplay?: (v: unknown) => unknown;
  toStorage?: (v: unknown) => unknown;
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

const TYPE_TRANSFORMS: Record<string, {
  toDisplay?: (v: unknown) => unknown;
  toStorage?: (v: unknown) => unknown;
}> = {
  Date: { toDisplay: dateToDisplay },
  DateTime: { toDisplay: datetimeToDisplay, toStorage: datetimeToStorage }
}

export const toDisplay = (field: string, v: unknown) =>
  FIELD_TRANSFORMS[field]?.toDisplay?.(v) ?? TYPE_TRANSFORMS[COLUMN_TYPES[field] ?? '']?.toDisplay?.(v) ?? v;

export const toStorage = (field: string, v: unknown) =>
  FIELD_TRANSFORMS[field]?.toStorage?.(v) ?? TYPE_TRANSFORMS[COLUMN_TYPES[field] ?? '']?.toStorage?.(v) ?? v;

/** 字段名级别默认值生成器（优先匹配） */
const FIELD_DEFAULTS: Record<string, () => unknown> = {
  month: () => {
    const { year, month } = getMajorityMonthForWeek(new Date);
    return `${String(year).slice(-2)}${String(month).padStart(2, '0')}`;
  }
};

/** 渲染器类型级别默认值生成器（字段名未匹配时使用） */
const TYPE_DEFAULTS: Record<string, () => unknown> = {
  Date: () => dateToDisplay(new Date()),
  DateTime: () => new Date().toISOString(),
  Boolean: () => 0,
};

/** 根据字段名获取存储格式的默认值。 */
export function getFieldDefault(field: string): unknown {
  return FIELD_DEFAULTS[field]?.() ?? TYPE_DEFAULTS[COLUMN_TYPES[field] ?? '']?.() ?? null;
}

