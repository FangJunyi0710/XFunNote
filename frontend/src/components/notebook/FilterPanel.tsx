import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { genId } from '@/lib/utils';
import type { FilterOp } from '@/types/filter';

// 后端 op 值映射：前端 FilterOp → 后端 op 字符串
const OP_MAP: Record<FilterOp, string> = {
  eq: '=',
  neq: '!=',
  gt: '>',
  ge: '>=',
  lt: '<',
  le: '<=',
  like: 'LIKE',
  in: 'IN',
};

interface FilterRow {
  id: string;
  column: string;
  op: FilterOp;
  value: string;
}

interface FilterPanelProps {
  columns: { name: string; type: string }[];
  onApply: (filterJson: string | null) => void;
}

const FILTER_OPS: { value: FilterOp; label: string }[] = [
  { value: 'eq', label: '=' },
  { value: 'neq', label: '!=' },
  { value: 'gt', label: '>' },
  { value: 'ge', label: '>=' },
  { value: 'lt', label: '<' },
  { value: 'le', label: '<=' },
  { value: 'like', label: '包含' },
];

export const FilterPanel: React.FC<FilterPanelProps> = ({ columns, onApply }) => {
  const [rows, setRows] = useState<FilterRow[]>([]);

  const addRow = () => {
    if (columns.length === 0) return;
    setRows((prev) => [
      ...prev,
      { id: genId(), column: columns[0].name, op: 'eq', value: '' },
    ]);
  };

  const updateRow = (id: string, field: keyof FilterRow, val: string) => {
    setRows((prev) =>
      prev.map((r) => (r.id === id ? { ...r, [field]: val } : r)),
    );
  };

  const removeRow = (id: string) => {
    setRows((prev) => prev.filter((r) => r.id !== id));
  };

  const applyFilter = () => {
    const valid = rows.filter((r) => r.value.trim() !== '');
    if (valid.length === 0) {
      onApply(null);
      return;
    }

    // DNF 格式：[[{column, op, value}, ...]]，外层 OR、内层 AND
    const dnf = [valid.map((r) => ({
      column: r.column,
      op: OP_MAP[r.op],
      value: r.value,
    }))];
    onApply(JSON.stringify(dnf));
  };

  const clearFilter = () => {
    setRows([]);
    onApply(null);
  };

  return (
    <Card className="mb-4">
      <CardContent className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">筛选条件</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={addRow}>
              + 添加条件
            </Button>
            {rows.length > 0 && (
              <>
                <Button variant="ghost" size="sm" onClick={clearFilter}>
                  清除
                </Button>
                <Button size="sm" onClick={applyFilter}>
                  应用
                </Button>
              </>
            )}
          </div>
        </div>

        {rows.map((row) => (
          <div key={row.id} className="flex items-center gap-2">
            <Select
              value={row.column}
              onChange={(e) => updateRow(row.id, 'column', e.target.value)}
              className="w-36"
            >
              {columns.map((col) => (
                <option key={col.name} value={col.name}>
                  {col.name}
                </option>
              ))}
            </Select>

            <Select
              value={row.op}
              onChange={(e) => updateRow(row.id, 'op', e.target.value)}
              className="w-24"
            >
              {FILTER_OPS.map((op) => (
                <option key={op.value} value={op.value}>
                  {op.label}
                </option>
              ))}
            </Select>

            <Input
              value={row.value}
              onChange={(e) => updateRow(row.id, 'value', e.target.value)}
              placeholder="值"
              className="flex-1"
            />

            <Button
              variant="ghost"
              size="sm"
              onClick={() => removeRow(row.id)}
              className="text-destructive"
            >
              ✕
            </Button>
          </div>
        ))}

        {rows.length === 0 && (
          <p className="text-xs text-muted-foreground">
            点击"添加条件"设置筛选，支持 AND 组合
          </p>
        )}
      </CardContent>
    </Card>
  );
};
