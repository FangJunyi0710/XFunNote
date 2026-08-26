// 筛选 DSL 类型
// 对应 xfun/core/filter.py 中的 Filter DNF 结构

import { genId } from "@/lib/utils";
import { useEffect, useRef, useState } from "react";

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
  col: string;
  op: FilterOp;
  val: unknown;
}

// 递归结构：外层 OR、内层 AND，元素为子树，直至叶子节点，最外层支持 (... , negate) 元组对整个结果取反。
export type Filter = Condition | Filter[][] | [Filter, boolean];

export const isCondition = (filter: Filter): filter is Condition =>
  !Array.isArray(filter);

export const isNegation = (filter: Filter): filter is [Filter, boolean] =>
  Array.isArray(filter) && typeof filter[1] === 'boolean';

export const isDNF = (filter: Filter): filter is Filter[][] =>
  Array.isArray(filter) && typeof filter[1] !== 'boolean';

export const isEmpty = (filter: Filter): filter is [] =>
  isDNF(filter) && filter.length === 0

export type Leaf = Condition | [Condition, boolean];
export const isLeaf = (flt: Filter): flt is Leaf => isCondition(flt) || isNegation(flt) && isCondition(flt[0]);
export const getCond = (leaf: Leaf): Condition => isNegation(leaf) ? leaf[0] : leaf;
export const setCond = (leaf: Leaf, newCond: Condition): Leaf => isNegation(leaf) ? [newCond, leaf[1]] : newCond;
export const getLeafNegate = (leaf: Leaf): boolean => isNegation(leaf) ? leaf[1] : false;
export const setLeafNegate = (leaf: Leaf, negate: boolean): Leaf => negate ? [getCond(leaf), true] : getCond(leaf);

export interface FilterRow<T = Filter> {
  id: string;
  filter: T;
}
export interface FilterGroup<T = Filter> {
  id: string;
  rows: FilterRow<T>[];
}

export interface FilterState<T = Filter> {
  groups: FilterGroup<T>[];
  negate: boolean;
}

export const isSimpleDNF = (groups: FilterGroup[]): groups is FilterGroup<Leaf>[] =>
  groups.every(g => g.rows.every(r => isLeaf(r.filter)));
export const flattenGroups = (groups: FilterGroup<Leaf>[]): [string, string, Leaf][] =>
  groups.flatMap(g => g.rows.map(r => [g.id, r.id, r.filter]));

export const filterToRow = (filter: Filter): FilterRow => 
  ({id: genId(), filter})

export const filterToGroup = (filter: Filter): FilterGroup =>
  ({id: genId(), rows: [{id: genId(), filter}]})

const DNFToGroups = (filter: Filter[][]): FilterGroup[] =>
  filter.map(g => ({id: genId(), rows: g.map(r => ({id: genId(), filter: r}))}))

const groupsToDNF = (groups: FilterGroup[]): Filter[][] =>
  groups.map(g => g.rows.map(r => r.filter))

const simplifyFilter = (filter: Filter): Filter => {
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

export const toState = (filter: Filter): FilterState => {
  if (isCondition(filter)) {
    return {groups: [filterToGroup(filter)], negate: false};
  }
  if (isDNF(filter)) {
    return {groups: DNFToGroups(filter), negate: false};
  }
  const result = toState(filter[0]);
  return {groups: result.groups, negate: result.negate !== filter[1]};
};

export const toFilter = (state: FilterState): Filter =>
  simplifyFilter([groupsToDNF(state.groups), state.negate]);

export const useFilterState = (value: Filter, onChange: (filter: Filter | null) => void, defaultCond: () => Condition) => {
  const [state, setState] = useState<FilterState>(() => toState(value));
  const setGroups = (action: React.SetStateAction<FilterGroup[]>): void => setState(prev => ({...prev, groups: typeof action === 'function' ? action(prev.groups) : action}));
  const setNegate = (action: React.SetStateAction<boolean>): void => setState(prev => ({...prev, negate: typeof action === 'function' ? action(prev.negate) : action}));

  const onChangeRef = useRef(onChange);
  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  useEffect(() => {
    onChangeRef.current(state.groups.length === 0 ? null : toFilter(state));
  }, [state]);

  const addGroup = (cond?: Filter) => setGroups(prev => [...prev, filterToGroup(cond ?? defaultCond())]);
  const removeGroup = (gid: string) => setGroups(prev => prev.filter(g => g.id !== gid));
  const addRow = (gid: string, cond?: Filter) => setGroups(prev => prev.map(g => g.id === gid ? {...g, rows: [...g.rows, filterToRow(cond ?? defaultCond())]} : g));
  const updateRow = (gid: string, rid: string, newLeaf: Filter) => setGroups(prev => prev.map(g => g.id === gid ? {...g, rows: g.rows.map(r => r.id === rid ? {...r, filter: newLeaf} : r)} : g));
  const removeRow = (gid: string, rid: string) => setGroups(prev => prev.map(g => g.id === gid ? {...g, rows: g.rows.filter(r => r.id !== rid)} : g).filter(g => g.rows.length > 0));

  const clearGroups = () => {setGroups([]); setNegate(false); };
  return {
    state,
    setState,
    setGroups,
    setNegate,
    addGroup,
    removeGroup,
    clearGroups,
    addRow,
    updateRow,
    removeRow
  };
};

export type View = Record<string, [string[], Filter][]>;
