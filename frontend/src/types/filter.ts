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

export interface FilterRow {
  id: string;
  filter: Filter;
}
export interface FilterGroup {
  id: string;
  rows: FilterRow[];
}

export interface DNFFilterState {
  groups: FilterGroup[];
  negate?: boolean;
}

export const filterToRow = (filter: Filter): FilterRow => 
  ({id: genId(), filter})

export const filterToGroup = (filter: Filter): FilterGroup =>
  ({id: genId(), rows: [{id: genId(), filter}]})

const DNFToGroups = (filter: Filter[][]): FilterGroup[] =>
  filter.map(g => ({id: genId(), rows: g.map(r => ({id: genId(), filter: r}))}))

const groupsToDNF = (groups: FilterGroup[]): Filter[][] =>
  groups.map(g => g.rows.map(r => r.filter))

export const simplifyFilter = (filter: Filter): Filter => {
  if (isCondition(filter)) {
    return filter;
  }
  if (isDNF(filter)) {
    const result = filter.map(g => g.map(r => simplifyFilter(r)).filter(r => !isDNF(r) || r.length)).filter(g => g.length);
    if (result.length === 1 && result[0]?.length === 1) {
      return result[0][0]!;
    }
    return result;
  }
  const result = simplifyFilter(filter[0]);
  return filter[1] ? isNegation(result) ? result[0] : [result, true] : result;
};

const toStateInner = (filter: Filter): DNFFilterState => {
  if (isCondition(filter)) {
    return {groups: [filterToGroup(filter)]};
  }
  if (isDNF(filter)) {
    return {groups: DNFToGroups(filter)};
  }
  const result = toStateInner(filter[0]);
  return {groups: result.groups, negate: result.negate !== filter[1]};
};

export const toState = (filter: Filter): DNFFilterState =>
  toStateInner(filter);

export const toFilter = (state: DNFFilterState): Filter =>
  [groupsToDNF(state.groups), state.negate ?? false];

export const toStandardFilter = (filter: Filter): [Filter[][], boolean] => {
  if (isCondition(filter)) {
    return [[[filter]], false];
  }
  if (isDNF(filter)) {
    return [[[filter]], false];
  }
  const result = toStandardFilter(filter[0]);
  return [result[0], result[1] === filter[1]];
};
  
