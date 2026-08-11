// 笔记本核心类型
import type { EntryTypeMap, NotebookType } from "@/config/notebook";

/** Schema 中单个列的描述 */
export interface ColumnDef {
  name: string;
  type: string;
  required: boolean;
  auto: boolean;
}

/** 完整的笔记本 Schema */
export interface NotebookSchema {
  name: NotebookType;
  columns: ColumnDef[];
}

export type Entry = Record<string, unknown>;

export const asEntry = <T extends NotebookType>(
  _type: T,
  raw: Entry,
): EntryTypeMap[T] => {
  return raw as unknown as EntryTypeMap[T];
}

export type OrderBy = [string, 'ASC' | 'DESC'][];
