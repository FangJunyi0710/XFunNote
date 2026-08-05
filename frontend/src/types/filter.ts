// 筛选 DSL 类型
// 对应 xfun/core/filter.py 中的 Filter DNF 结构

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

export interface FilterState {
  filter: Filter[][];
  negate?: boolean;
}

const simplifyFilter = (filter: Filter): Filter => {
  if (isCondition(filter)) {
    return filter;
  }
  if (isDNF(filter)) {
    const result = filter.map((g) => g.map((r) => simplifyFilter(r)).filter((r) => !isDNF(r) || r.length)).filter((g) => g.length);
    if (result.length === 1 && result[0]?.length === 1) {
      return result[0][0]!;
    }
    return result;
  }
  const result = simplifyFilter(filter[0]);
  return filter[1] ? isNegation(result) ? result[0] : [result, true] : result;
};

const toStateInner = (filter: Filter): FilterState => {
  if (isCondition(filter)) {
    return {filter: [[filter]]};
  }
  if (isDNF(filter)) {
    return {filter};
  }
  const result = toStateInner(filter[0]);
  return {filter: result.filter, negate: result.negate !== filter[1]};
};

export const toState = (filter: Filter): FilterState =>
  toStateInner(simplifyFilter(filter));

export const toFilter = (state: FilterState): Filter =>
  simplifyFilter([state.filter, state.negate ?? false]);
