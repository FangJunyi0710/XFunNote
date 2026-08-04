// 筛选 DSL 类型
// 对应 xfun/core/filter.py 中的 Filter DNF 结构

import { genId } from "@/lib/utils";

export type FilterOp = '=' | '>' | '<' | '>=' | '<=' | 'BETWEEN' | 'GLOB';

export const FILTER_OPS_LABEL: Record<FilterOp, string> = {
  GLOB: '匹配通配符', 
  BETWEEN: '介于两值间',
  '=': '=',
  '<=': '<=',
  '>=': '>=',
  '<': '<',
  '>': '>',
};


export interface Condition {
  column: string;
  op: FilterOp;
  value: unknown;
}

// 递归结构：外层 OR、内层 AND，元素为子树，直至叶子节点，最外层支持 (... , negate) 元组对整个结果取反。
export type Filter = Condition | Filter[][] | [Filter, boolean];

export const isCondition = (filter: Filter): filter is Condition =>
  !Array.isArray(filter);

export const isNegation = (filter: Filter): filter is [Filter, boolean] =>
  Array.isArray(filter) && typeof filter[1] === 'boolean';

export const isDNF = (filter: Filter): filter is Filter[][] =>
  Array.isArray(filter) && typeof filter[1] !== 'boolean';

export interface FlatFilterState {
  filter: Filter;
  negate?: boolean;
}

export interface ConditionRow {
  id: string;
  leaf: FlatFilterState;
}

export const conditionToRow = (filter: Filter): ConditionRow =>
  ({id: genId(), leaf: {filter}});

export interface ConditionGroup {
  id: string;
  rows: ConditionRow[];
}

export const conditionToGroup = (filter: Filter): ConditionGroup =>
  ({id: genId(), rows: [conditionToRow(filter)]});

export interface DNFFilterState {
  filter: ConditionGroup[];
  negate?: boolean;
}

export type FilterState = DNFFilterState | FlatFilterState;

export const isDNFState = (state: FilterState): state is DNFFilterState =>
  Array.isArray(state.filter) && state.filter[0] && 'id' in state.filter[0];

export const toDNFState = (state: FilterState): DNFFilterState => {
  if (isDNFState(state)) return state;
  if (isCondition(state.filter)) {
    return {filter: [conditionToGroup(state.filter)], negate: state.negate ?? false};
  }
  if (isDNF(state.filter)) {
    return {filter: state.filter.map((g) => ({id: genId(), rows: g.map((r) => ({id: genId(), leaf: {filter: r}}))}))};
  }
  return {filter: [conditionToGroup(state.filter[0])], negate: state.filter[1] !== state.negate};
};

export const toFlatState = (state: FilterState): FlatFilterState =>
  isDNFState(state) ? {filter: state.filter.map((g) => g.rows.map((r) => r.leaf.negate ? [r.leaf.filter, true] : r.leaf.filter)), negate: state.negate ?? false} : state;
