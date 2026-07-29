// 筛选 DSL 类型
// 对应 xfun/core/filter.py 中的 Filter DNF 结构

export type FilterOp = '=' | '!=' | '>' | '<' | '>=' | '<=' | 'LIKE' | 'IN' | 'BETWEEN' | 'TEXT_SEARCH';

export const FILTER_OPS_LABEL: Record<FilterOp, string> = {
  '=': '=',
  '!=': '!=',
  '>': '>',
  '>=': '>=',
  '<': '<',
  '<=': '<=',
  LIKE: 'like', 
  IN: 'in',
  BETWEEN: 'between',
  TEXT_SEARCH: 'contains',
};


export interface Condition {
  column: string;
  op: FilterOp;
  value: unknown;
}

export type Filter = Condition[][];

export interface ConditionRow {
  id: string;
  cond: Condition;
}

export interface ConditionGroup {
  id: string;
  rows: ConditionRow[];
}
