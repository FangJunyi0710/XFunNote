import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { genId } from '@/lib/utils';
import { FILTER_OPS_LABEL, type ConditionGroup, type ConditionRow, type DNF, type FilterOp } from '@/types/filter';
import { CloseIcon, SubmitIcon } from '@/components/ui/icons';
import { ValueEditor } from './ValueEditor';
import type { ColumnDef } from '@/types/notebook';

function tryParseNumber(s: string): string | number {
  const n = Number(s);
  return !isNaN(n) && s.trim() !== '' ? n : s;
}

function serializeValue(op: FilterOp, display: string): string | number[] | string[] {
  if (op === 'IN') {
    return display.split(',').map(s => s.trim()).filter(Boolean);
  }
  if (op === 'BETWEEN') {
    const parts = display.split(',').map(s => s.trim());
    return parts.length !== 2 ? '' : parts.map(tryParseNumber).filter((v): v is number => typeof v === 'number');
  }
  return display;
}

function deserializeValue(op: FilterOp, raw: string | number[] | string[]): string {
  if (Array.isArray(raw)){
    return raw.join(', ');
  }
  if (op === 'IN') {
    try {
      const arr = JSON.parse(raw);
      if (Array.isArray(arr)){
        return arr.join(', ');
      }
    } catch {}
    return raw;
  }
  return raw;
}

function parseDNF(json: string | null): ConditionGroup[] {
  if (!json) return [];
  try {
    const dnf: DNF = JSON.parse(json);
    return dnf.map(group => ({
      id: genId(),
      rows: group.map(cond => {
        return {
          id: genId(),
          column: cond.column,
          op: cond.op as FilterOp,
          value: deserializeValue(cond.op as FilterOp, cond.value)
        };
      }),
    }));
  } catch { return []; }
}
function serializeDNF(groups: ConditionGroup[]): string | null {
  const valid = groups.map(g => g.rows.filter(r => r.value.trim() !== '')).filter(rows => rows.length > 0);
  if (valid.length === 0){
    return null;
  }
  const dnf: DNF = valid.map(rows =>
    rows.map(r => ({
      column: r.column,
      op: r.op,
      value: serializeValue(r.op, r.value)
    }))
  );
  return JSON.stringify(dnf);
}

interface FilterEditorProps {
  columns: ColumnDef[];
  initialFilter?: string | null;
  onApply: (filterJson: string | null) => void;
  onChange?: (filterJson: string | null) => void;
}

export const FilterEditor: React.FC<FilterEditorProps> = ({ columns, initialFilter, onApply, onChange }) => {
  const [groups, setGroups] = useState<ConditionGroup[]>(() => {
    const parsed = parseDNF(initialFilter ?? null);
    return parsed.length > 0 ? parsed : [];
  });

  useEffect(() => { onChange?.(serializeDNF(groups)); }, [groups]);

  const addGroup = () => setGroups(prev => [...prev, { id: genId(), rows: [{ id: genId(), column: columns[0]?.name || '', op: '=' as FilterOp, value: '' }] }]);
  const removeGroup = (gid: string) => setGroups(prev => prev.filter(g => g.id !== gid));
  const addRow = (gid: string) => setGroups(prev => prev.map(g => g.id === gid ? { ...g, rows: [...g.rows, { id: genId(), column: columns[0]?.name || '', op: '=' as FilterOp, value: '' }] } : g));
  const updateRow = (gid: string, rid: string, patch: Partial<ConditionRow>) => setGroups(prev => prev.map(g => g.id === gid ? { ...g, rows: g.rows.map(r => r.id === rid ? { ...r, ...patch } : r) } : g));
  const removeRow = (_gid: string, rid: string) => setGroups(prev => prev.map(g => ({ ...g, rows: g.rows.filter(r => r.id !== rid) })).filter(g => g.rows.length > 0));
  
  // ─── 辅助：IN 列表项操作 ──────────────────────────────────────────────
  const splitInValues = (value: string): string[] => value.split(',').map(s => s.trim()).filter(Boolean);
  const joinInValues = (items: string[]): string => items.join(', ');

  const addInItem = (gid: string, rid: string) => setGroups(prev => prev.map(g => g.id === gid ? { ...g, rows: g.rows.map(r => r.id === rid ? { ...r, value: joinInValues([...splitInValues(r.value), '']) } : r)} : g));
  const removeInItem = (gid: string, rid: string, index: number) => setGroups(prev => prev.map(g => g.id !== gid ? g : { ...g, rows: g.rows.map(r => r.id !== rid ? r : ((items) => items.length <= 1 ? r : { ...r, value: joinInValues(items.filter((_, i) => i !== index)) })(splitInValues(r.value))) }));
  
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
    const colDef = columns.find((c) => c.name === row.column)!;

    const handleValueChange = (newVal: unknown) => {
      const strVal = newVal === null || newVal === undefined ? '' : String(newVal);
      updateRow(groupId, row.id, { value: strVal });
    };

    const handleInItemChange = (index: number, newVal: string) => {
      const items = splitInValues(row.value);
      items[index] = newVal;
      updateRow(groupId, row.id, { value: joinInValues(items) });
    };

    // ── 查找表：运算符 → 值区域渲染函数 ──
    const opRenderers: Record<FilterOp, (row: ConditionRow) => React.ReactNode> = {
      '=': (r) => <ValueEditor col={colDef} value={r.value} onChange={handleValueChange} className="flex-1" />,
      '!=': (r) => <ValueEditor col={colDef} value={r.value} onChange={handleValueChange} className="flex-1" />,
      '>': (r) => <ValueEditor col={colDef} value={r.value} onChange={handleValueChange} className="flex-1" />,
      '<': (r) => <ValueEditor col={colDef} value={r.value} onChange={handleValueChange} className="flex-1" />,
      '>=': (r) => <ValueEditor col={colDef} value={r.value} onChange={handleValueChange} className="flex-1" />,
      '<=': (r) => <ValueEditor col={colDef} value={r.value} onChange={handleValueChange} className="flex-1" />,
      'LIKE': (r) => <ValueEditor col={colDef} value={r.value} onChange={handleValueChange} className="flex-1" />,
      'TEXT_SEARCH': (r) => <ValueEditor col={colDef} value={r.value} onChange={handleValueChange} className="flex-1" />,
      'BETWEEN': (r) => {
        const parts = r.value.split(',').map((s) => s.trim());
        const min = parts[0] || '';
        const max = parts[1] || '';
        return (
          <div className="flex items-center gap-1 flex-1">
            <Input
              value={min}
              onChange={(e) => handleValueChange(`${e.target.value},${max}`)}
              placeholder="最小值"
              className="flex-1"
            />
            <span className="text-muted-foreground">~</span>
            <Input
              value={max}
              onChange={(e) => handleValueChange(`${min},${e.target.value}`)}
              placeholder="最大值"
              className="flex-1"
            />
          </div>
        );
      },
      'IN': (r) => {
        const items = splitInValues(r.value);
        return (
          <div className="flex-1 space-y-1">
            {items.map((item, idx) => (
              <div key={idx} className="flex items-center gap-1">
                <Input
                  value={item}
                  onChange={(e) => handleInItemChange(idx, e.target.value)}
                  placeholder={`项 ${idx + 1}`}
                  className="flex-1"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeInItem(groupId, row.id, idx)}
                  className="text-destructive h-7 w-7 p-0"
                  disabled={items.length <= 1}
                >
                  ×
                </Button>
              </div>
            ))}
          </div>
        );
      },
    };

    // 根据运算符获取渲染函数
    const renderValueArea = opRenderers[row.op];

    const renderTopRow = () => {
      const isInOp = row.op === 'IN';
      return (
        <div className="flex items-center gap-2">
          <Select value={row.column} onChange={e => updateRow(groupId, row.id, { column: e.target.value })} className="w-36">
            {columns.map(col => <option key={col.name} value={col.name}>{col.name}</option>)}
          </Select>
          <Select value={row.op} onChange={e => updateRow(groupId, row.id, { op: e.target.value as FilterOp, value: '' })} className="w-24">
            {Object.entries(FILTER_OPS_LABEL).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </Select>
          <div className="flex-1" />
          {isInOp && (
            <Button variant="outline" size="sm" onClick={() => addInItem(groupId, row.id)}>
              + 添加项
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={() => removeRow(groupId, row.id)} className="text-destructive">×</Button>
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
