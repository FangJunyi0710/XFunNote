import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { conditionToGroup, conditionToRow, toDNFState, toFlatState, type Condition, type ConditionGroup, type ConditionRow, type DNFFilterState, type Filter, type FilterOp, type FilterState, type FlatFilterState } from '@/types/filter';
import { CloseIcon } from '@/components/ui/icons';
import type { ColumnDef } from '@/types/notebook';

export const parseFilterJSON = (json: string | null): FlatFilterState => {
  if (!json) return {filter: []};
  try {
    return {filter: JSON.parse(json)};
  } catch {
    return {filter: []};
  }
}

// ─── 序列化内部状态为 JSON 字符串（Filter） ──────────────────────
export const serializeFilter = (state: FilterState): string => {
  const flat = toFlatState(state);
  return JSON.stringify(flat.negate ? [flat.filter, true] : flat.filter);
}

const FlatFilterEditor: React.FC<{
  columns: ColumnDef[];
  value: FlatFilterState;
  onChange?: (state: FlatFilterState | null) => void;
}> = ({columns, value, onChange}) => {
  const defaultCond: Condition = {column: columns[0]?.name ?? '', op: 'GLOB' as FilterOp, value: null};
  const defaultLeaf: FlatFilterState = {filter: defaultCond};
  const [filter, setFilter] = useState<Filter>(() => value.filter);
  const [negate, setNegate] = useState<boolean>(() => value.negate ?? false)

  useEffect(() => { onChange?.({filter, negate}); }, [filter, negate]);

  if (!columns[0]?.name) {
    return null;
  }

  return null;
};

const DNFFilterEditor: React.FC<{
  columns: ColumnDef[];
  value: DNFFilterState;
  onChange?: (state: DNFFilterState | null) => void;
}> = ({columns, value, onChange}) => {
  const defaultCond: Condition = {column: columns[0]?.name ?? '', op: 'GLOB' as FilterOp, value: null};
  const [groups, setGroups] = useState<ConditionGroup[]>(() => value.filter);
  const [negate, setNegate] = useState<boolean>(() => value.negate ?? false)

  useEffect(() => { onChange?.({filter: groups, negate}); }, [groups, negate]);

  if (!columns[0]?.name) {
    return null;
  }

  const addGroup = () => setGroups(prev => [...prev, conditionToGroup(defaultCond)]);
  const removeGroup = (gid: string) => setGroups(prev => prev.filter(g => g.id !== gid));
  const addRow = (gid: string) => setGroups(prev => prev.map(g => g.id === gid ? { ...g, rows: [...g.rows, conditionToRow(defaultCond)] } : g));
  const updateRow = (gid: string, rid: string, newLeaf: FlatFilterState) => setGroups(prev => prev.map(g => g.id === gid ? { ...g, rows: g.rows.map(r => r.id === rid ? { ...r, leaf: newLeaf } : r) } : g));
  const removeRow = (_gid: string, rid: string) => setGroups(prev => prev.map(g => ({ ...g, rows: g.rows.filter(r => r.id !== rid) })).filter(g => g.rows.length > 0));

  const handleClear = () => setGroups([]);

  const renderHeader = () => (
    <div className="flex items-center justify-between">
      <span className="text-sm font-medium">筛选条件</span>
      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={addGroup}>+ OR 组</Button>
        <Button variant="ghost" size="sm" onClick={handleClear} title="清除"><CloseIcon /></Button>
      </div>
    </div>
  );

  const renderOrSeparator = () => (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <div className="flex-1 border-t" />
      <span className="font-semibold text-orange-500">OR</span>
      <div className="flex-1 border-t" />
    </div>
  );

  const renderRow = (row: ConditionRow, groupId: string) => {
    return <FilterEditor key={row.id} columns={columns} value={row.leaf}
      onChange={(state) => state ? updateRow(groupId, row.id, toFlatState(state)) : removeRow(groupId, row.id)}
    />;
  };

  const renderGroup = (group: ConditionGroup, index: number) => (
    <div key={group.id} className="space-y-2">
      {index > 0 && renderOrSeparator()}
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">AND 组 {index + 1}</span>
        <div className="flex gap-1">
          <Button variant="ghost" size="sm" onClick={() => addRow(group.id)}>+ 条件</Button>
          <Button variant="ghost" size="sm" onClick={() => removeGroup(group.id)} className="text-destructive">删除组</Button>
        </div>
      </div>
      {group.rows.map(row => renderRow(row, group.id))}
    </div>
  );

  const renderEmptyState = () => <p className="text-xs text-muted-foreground">点击"OR 组"添加一组条件，同一组内条件为 AND 关系</p>;

  return (
    <Card className="mb-4">
      <CardContent className="p-4 space-y-4">
        {renderHeader()}
        {groups.map((group, gi) => renderGroup(group, gi))}
        {groups.length === 0 && renderEmptyState()}
      </CardContent>
    </Card>
  );
};

export const FilterEditor: React.FC<{
  columns: ColumnDef[];
  value?: FilterState;
  onChange?: (state: FilterState | null) => void;
}> = ({ columns, value, onChange }) => {
  const [isDNFMode, setIsDNFMode] = useState(false);
  const [state, setState] = useState<FilterState>(() => value ?? {filter: []});

  if (!columns[0]?.name) {
    return null;
  }

  if (isDNFMode) {
    return <DNFFilterEditor columns={columns} value={toDNFState(state)} onChange={(state) => onChange?.(state)} />;
  } else {
    return <FlatFilterEditor columns={columns} value={toFlatState(state)} onChange={(state) => onChange?.(state)} />;
  }
};
// TODO 实现完整的 filter 编辑器 含双重取反、均列表、引用等
// TODO 添加新组等时，取之前值作为初始值。
