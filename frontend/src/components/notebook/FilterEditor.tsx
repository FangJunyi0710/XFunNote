import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { conditionToGroup, conditionToRow, toDNFState, toFlatState, type Condition, type ConditionGroup, type ConditionRow, type DNFFilterState, type Filter, type FilterOp, type FilterState, type FlatFilterState } from '@/types/filter';
import { ArrowIcon, CloseIcon, PlusIcon } from '@/components/ui/icons';
import type { ColumnDef } from '@/types/notebook';
import { cn } from '@/lib/utils';
import { Switch } from '../ui/switch';

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
  onChange: (state: FlatFilterState | null) => void;
}> = ({columns, value, onChange}) => {
  const defaultCond: Condition = {column: columns[0]?.name ?? '', op: 'GLOB' as FilterOp, value: null};
  const defaultLeaf: FlatFilterState = {filter: defaultCond};
  const [filter, setFilter] = useState<Filter>(() => value.filter);
  const [negate, setNegate] = useState<boolean>(() => value.negate ?? false)

  useEffect(() => { onChange({filter, negate}); }, [filter, negate]);

  return serializeFilter(value);
};

const DNFFilterEditor: React.FC<{
  columns: ColumnDef[];
  value: DNFFilterState;
  onChange: (state: DNFFilterState | null) => void;
}> = ({columns, value, onChange}) => {
  const defaultCond: Condition = {column: columns[0]?.name ?? '', op: 'GLOB' as FilterOp, value: null};
  const [groups, setGroups] = useState<ConditionGroup[]>(() => value.filter);
  const [negate, setNegate] = useState<boolean>(() => value.negate ?? false)

  useEffect(() => { onChange({filter: groups, negate}); }, [groups, negate]);

  const addGroup = () => setGroups(prev => [...prev, conditionToGroup(defaultCond)]);
  const removeGroup = (gid: string) => setGroups(prev => prev.filter(g => g.id !== gid));
  const addRow = (gid: string) => setGroups(prev => prev.map(g => g.id === gid ? { ...g, rows: [...g.rows, conditionToRow(defaultCond)] } : g));
  const updateRow = (gid: string, rid: string, newLeaf: FlatFilterState) => setGroups(prev => prev.map(g => g.id === gid ? { ...g, rows: g.rows.map(r => r.id === rid ? { ...r, leaf: newLeaf } : r) } : g));
  const removeRow = (_gid: string, rid: string) => setGroups(prev => prev.map(g => ({ ...g, rows: g.rows.filter(r => r.id !== rid) })).filter(g => g.rows.length > 0));

  const handleClear = () => {setGroups([]); setNegate(false); };

  return (
    <Card className="ring-1">
      <CardContent className="">
        {/** 编辑器首行 */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">分类讨论</span>
          <div className="flex gap-2 items-center">
            {negate && <p>排除下列情况</p>}
            <Switch checked={negate} onCheckedChange={() => setNegate(prev => !prev)} />
            <Button variant={groups.length ? 'outline' : 'default'} size="sm" onClick={addGroup} type="button" title='添加情况'><PlusIcon/></Button>
            <Button variant="ghost" size="sm" onClick={handleClear} type="button" title="清除"><CloseIcon /></Button>
          </div>
        </div>
        {/** 渲染条件组 */}
        {groups.map((group, index) => <div key={group.id} className="space-y-2">
          {/** 分隔符 */}
          {index > 0 && <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <div className="flex-1 border-t" />
            <span className="font-semibold text-orange-500">OR</span>
            <div className="flex-1 border-t" />
          </div>}
          {/** 条件组首行 */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">情况 {index + 1}</span>
            <div className="flex gap-1">
              <Button variant="ghost" size="sm" type="button" onClick={() => addRow(group.id)}>+ 条件</Button>
              <Button variant="ghost" size="sm" type="button" onClick={() => removeGroup(group.id)} className="text-destructive">删除组</Button>
            </div>
          </div>
          {/** 条件组各条件 */}
          {group.rows.map(row => <FilterEditor key={row.id} columns={columns} value={row.leaf}
            onChange={(state) => state ? updateRow(group.id, row.id, toFlatState(state)) : removeRow(group.id, row.id)}
          />)}
        </div>)}
      </CardContent>
    </Card>
  );
};

export const FilterEditor: React.FC<{
  columns: ColumnDef[];
  value: FilterState;
  onChange: (state: FilterState | null) => void;
}> = ({ columns, value, onChange }) => {
  const [isDNFMode, setIsDNFMode] = useState(false);
  if (!columns[0]?.name) return null;

  return <div className='relative'>
    <Button variant='ghost' type="button" className='absolute top-0 -right-3 z-10' onClick={() => setIsDNFMode(prev => !prev)}>
      <ArrowIcon direction="left" className={cn('transition-transform duration-100 origin-center', isDNFMode && '-rotate-90')}/>
    </Button>
    {isDNFMode ? <DNFFilterEditor columns={columns} value={toDNFState(value)} onChange={(state) => onChange(state)} />
    : <FlatFilterEditor columns={columns} value={toFlatState(value)} onChange={(state) => onChange(state)} />}
  </div>;
};
// TODO 实现完整的 filter 编辑器 含双重取反、均列表、引用等
// TODO 添加新组等时，取之前值作为初始值。
