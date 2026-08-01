// 筛选 DSL 类型
// 对应 xfun/core/filter.py 中的 Filter DNF 结构

export type FilterOp = '=' | '!=' | '>' | '<' | '>=' | '<=' | 'IN' | 'BETWEEN' | 'GLOB';

export const FILTER_OPS_LABEL: Record<FilterOp, string> = {
  '=': '=',
  '!=': '!=',
  '>': '>',
  '>=': '>=',
  '<': '<',
  '<=': '<=',
  GLOB: '匹配通配符', 
  IN: '包含于列表',
  BETWEEN: '介于两值间',
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
