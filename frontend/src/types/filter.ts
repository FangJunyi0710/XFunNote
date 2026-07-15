// 筛选 DSL 类型
// 对应 xfun/core/filter.py 中的 Filter DNF 结构

export type FilterOp = 'eq' | 'neq' | 'lt' | 'le' | 'gt' | 'ge' | 'like' | 'in' | 'not_like' | 'not_in' | 'between' | 'text_search';

export interface Condition {
  column: string;
  op: FilterOp;
  value: string | number | boolean | null | (string | number)[];
}

export interface FilterClause {
  or?: FilterClause[];
  and?: FilterClause[];
  cond?: Condition;
}

// 用于 UI 展示的扁平化条件行
export interface FilterRow {
  id: string;
  column: string;
  op: FilterOp;
  value: string;
  conjunction: 'AND' | 'OR';
}

export interface FilterGroup {
  id: string;
  rows: FilterRow[];
  conjunction: 'AND' | 'OR';
}
