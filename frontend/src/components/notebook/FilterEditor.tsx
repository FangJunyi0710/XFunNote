import React, { useState, useEffect, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { genId } from '@/lib/utils';
import { FILTER_OPS_LABEL, type Condition, type ConditionGroup, type ConditionRow, type Filter, type FilterOp } from '@/types/filter';
import { CloseIcon, DeleteIcon, PlusIcon, SubmitIcon } from '@/components/ui/icons';
import { ValueEditor } from './ValueEditor';
import type { ColumnDef } from '@/types/notebook';
import { getFieldLabel, sortColumns } from '@/config/notebook';

// ─── 解析后端 JSON（Filter）为内部状态（ConditionGroup[]） ──────
const parseDNF = (json: string | null): ConditionGroup[] => {
  if (!json) return [];
  try {
    const filter: Filter = JSON.parse(json);
    return filter.map(group => ({ id: genId(), rows: group.map(cond => ({ id: genId(), cond: cond })) }));
  } catch {
    return [];
  }
}

// ─── 序列化内部状态为 JSON 字符串（Filter） ──────────────────────
const serializeDNF = (groups: ConditionGroup[]): string => JSON.stringify(groups.map(g => g.rows.map(r => r.cond)));

export const FilterEditor: React.FC<{
  columns: ColumnDef[];
  initialFilter?: string | null;
  onApply: (filterJson: string | null) => void;
  onChange?: (filterJson: string | null) => void;
}> = ({ columns, initialFilter, onApply, onChange }) => {
  if (!columns[0]?.name) {
    return null;
  }
  const sortedColumns = useMemo(() => sortColumns(columns), [columns]);
  const defaultCond: Condition = {column: sortedColumns[0]?.name!, op: 'GLOB' as FilterOp, value: null};
  const [groups, setGroups] = useState<ConditionGroup[]>(() => {
    const parsed = parseDNF(initialFilter ?? null);
    return parsed.length > 0 ? parsed : [{id: genId(), rows: [{id: genId(), cond: defaultCond}]}];
  });

  useEffect(() => { onChange?.(serializeDNF(groups)); }, [groups]);

  const addGroup = () => setGroups(prev => [...prev, { id: genId(), rows: [{ id: genId(), cond: defaultCond }] }]);
  const removeGroup = (gid: string) => setGroups(prev => prev.filter(g => g.id !== gid));
  const addRow = (gid: string) => setGroups(prev => prev.map(g => g.id === gid ? { ...g, rows: [...g.rows, { id: genId(), cond: defaultCond }] } : g));
  const updateRow = (gid: string, rid: string, patch: Partial<Condition>) => setGroups(prev => prev.map(g => g.id === gid ? { ...g, rows: g.rows.map(r => r.id === rid ? { ...r, cond: { ...r.cond, ...patch } } : r) } : g));
  const removeRow = (_gid: string, rid: string) => setGroups(prev => prev.map(g => ({ ...g, rows: g.rows.filter(r => r.id !== rid) })).filter(g => g.rows.length > 0));

  // ─── 辅助：IN 列表项操作（直接操作数组） ──────────────────────────
  const addInItem = (gid: string, rid: string) => setGroups(prev => prev.map(g => g.id === gid ? { ...g, rows: g.rows.map(r => r.id === rid ? { ...r, cond: { ...r.cond, value: [...(Array.isArray(r.cond.value) ? r.cond.value : []), null] } } : r) } : g));
  const removeInItem = (gid: string, rid: string, index: number) => setGroups(prev => prev.map(g => g.id !== gid ? g : { ...g, rows: g.rows.map(r => r.id !== rid ? r : { ...r, cond: { ...r.cond, value: (Array.isArray(r.cond.value) ? r.cond.value : []).filter((_, i) => i !== index) } }) }));

  const handleApply = () => onApply(serializeDNF(groups));
  const handleClear = () => setGroups([]);

  const renderHeader = () => (
    <div className="flex items-center justify-between">
      <span className="text-sm font-medium">筛选条件</span>
      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={addGroup}>+ OR 组</Button>
        <Button variant="ghost" size="sm" onClick={handleClear} title="清除"><CloseIcon /></Button>
        <Button size="sm" onClick={handleApply} title="提交"><SubmitIcon /></Button>
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
    const colDef = columns.find((c) => c.name === row.cond.column)!;
    const handleValueChange = (newVal: unknown) => {
      updateRow(groupId, row.id, { value: newVal });
    };
    // ── 查找表：运算符 → 值区域渲染函数 ──
    const opRenderers: Partial<Record<FilterOp, (row: ConditionRow) => React.ReactNode>> = {
      'BETWEEN': (r) => {
        const arr = Array.isArray(r.cond.value) ? r.cond.value : [null, null];
        const min = arr[0] ?? null;
        const max = arr[1] ?? null;
        return (
          <div className="flex items-center gap-1 flex-1">
            <ValueEditor col={colDef} value={min} onChange={(e) => {
                const newArr = [e, max];
                updateRow(groupId, row.id, { value: newArr });
              }} placeholder="最小值"
            />
            <span className="text-muted-foreground"> - </span>
            <ValueEditor col={colDef} value={max} onChange={(e) => {
                const newArr = [min, e];
                updateRow(groupId, row.id, { value: newArr });
              }} placeholder="最大值"
            />
          </div>
        );
      },
      'IN': (r) => {
        const items = Array.isArray(r.cond.value) ? r.cond.value : [null];
        return (
          <div className="flex-1 space-y-1">
            {items.map((item, idx) => (
              <div key={idx} className="flex items-center gap-1">
                <ValueEditor col={colDef} value={item}
                  onChange={(e) => {
                    const newItems = [...items];
                    newItems[idx] = e;
                    updateRow(groupId, row.id, { value: newItems });
                  }}
                  placeholder={`第 ${idx + 1} 项`}
                />
                {!(idx === items.length - 1 && item) && <Button variant="outline" size="sm" onClick={() => removeInItem(groupId, row.id, idx)} className="text-destructive">
                  <DeleteIcon/>
                </Button>}
                {idx === items.length - 1 && <Button variant="outline" size="sm" onClick={() => addInItem(groupId, row.id)}>
                  <PlusIcon/>
                </Button>}
              </div>
            ))}
          </div>
        );
      },
    };

    // 根据运算符获取渲染函数
    const renderValueArea = opRenderers[row.cond.op] ?? ((r): React.ReactNode => <ValueEditor col={colDef} value={r.cond.value} onChange={handleValueChange} placeholder={`${getFieldLabel(r.cond.column)} ${FILTER_OPS_LABEL[r.cond.op]} 的值`} />);

    const renderTopRow = () => {
      return (
        <div className="flex items-center gap-2">
          <Select value={row.cond.column} onChange={e => updateRow(groupId, row.id, { column: e.target.value })} className="w-36">
            {sortedColumns.map(col => <option key={col.name} value={col.name}>{getFieldLabel(col.name)}</option>)}
          </Select>
          <Select value={row.cond.op} onChange={e => updateRow(groupId, row.id, { op: e.target.value as FilterOp })} className="w-24">
            {Object.entries(FILTER_OPS_LABEL).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </Select>
          <Button variant="outline" size="sm" onClick={() => removeRow(groupId, row.id)} className="text-destructive"><DeleteIcon/></Button>
        </div>
      );
    };

    return (
      <div key={row.id} className="space-y-1">
        {renderTopRow()}
        {renderValueArea(row)}
      </div>
    );
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
// TODO 实现完整的 filter 编辑器 含双重取反、均列表、引用等
