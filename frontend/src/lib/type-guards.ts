/**
 * 运行时类型转换工具。
 *
 * 利用后端返回的 Schema（ColumnDef[]）对每个字段按 SQLite 类型进行运行时转换，
 * 并将转换后的 Record 通过类型断言还原为具体条目类型。
 */

import type { ColumnDef, NotebookSchema } from '@/types/notebook';
import type {
  NotebookType,
  PlanEntry,
  DiaryEntry,
  WordEntry,
  AccumulationEntry,
  AimemoryEntry,
  TimelineEntry,
  ScheduleEntry,
} from '@/config/notebook';

// ── SQLite 类型 → JS 类型 运行时转换器 ────────────────────

/** SQLite 类型名到运行时解析函数的映射 */
export const SQLITE_TYPE_PARSERS: Record<string, (v: unknown) => unknown> = {
  TEXT:    (v) => (v === null || v === undefined ? null : String(v)),
  INTEGER: (v) => (v === null || v === undefined ? null : Number(v)),
  REAL:    (v) => (v === null || v === undefined ? null : Number(v)),
  BLOB:    (v) => (v === null || v === undefined ? null : String(v)),
};

/**
 * 将单条原始记录按 ColumnDef[] 进行字段类型转换。
 * 只转换 columns 中声明的字段，额外字段透传。
 */
export function castEntry(
  raw: Record<string, unknown>,
  columns: ColumnDef[],
): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const col of columns) {
    const rawValue = raw[col.name];
    const parser = SQLITE_TYPE_PARSERS[col.type];
    result[col.name] = parser ? parser(rawValue) : rawValue;
  }
  // 透传 columns 未声明的额外字段
  for (const key of Object.keys(raw)) {
    if (!(key in result)) result[key] = raw[key];
  }
  return result;
}

/** 批量转换 */
export function castEntries(
  rawList: Record<string, unknown>[],
  columns: ColumnDef[],
): Record<string, unknown>[] {
  return rawList.map((raw) => castEntry(raw, columns));
}

// ── 条目类型守卫（运行时类型断言 + 缺失字段警告） ──────────

/** 笔记本类型 → 具体条目类型的映射表 */
export interface EntryTypeMap {
  plan: PlanEntry;
  diary: DiaryEntry;
  word: WordEntry;
  accumulation: AccumulationEntry;
  aimemory: AimemoryEntry;
  timeline: TimelineEntry;
  schedule: ScheduleEntry;
}

/**
 * 将 Record 断言为具体的条目类型。
 *
 * @param type  笔记本类型
 * @param raw   已转换（castEntry）的记录
 * @param columns  Schema 列定义（用于检查必填字段缺失）
 * @returns 断言后的条目
 *
 * @example
 * const e = asEntry('plan', castEntry(raw, schema.columns), schema.columns);
 * e.no // 类型推断为 string ✓
 */
export function asEntry<T extends NotebookType>(
  type: T,
  raw: Record<string, unknown>,
  columns: ColumnDef[],
): EntryTypeMap[T] {
  // 开发环境下警告必填字段缺失
  if (import.meta.env.DEV) {
    for (const col of columns) {
      if (col.required && !col.name.startsWith('_') && raw[col.name] === undefined) {
        console.warn(`[type-guards] 条目缺失必填字段 "${col.name}"（类型: ${col.type}）`);
      }
    }
  }
  return raw as unknown as EntryTypeMap[T];
}

/**
 * 便捷函数：先 cast 再 asEntry
 */
export function castAndAsEntry<T extends NotebookType>(
  type: T,
  raw: Record<string, unknown>,
  columns: ColumnDef[],
): EntryTypeMap[T] {
  return asEntry(type, castEntry(raw, columns), columns);
}
