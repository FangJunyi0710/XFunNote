import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { genId } from '@/lib/utils';
import type { FilterOp } from '@/types/filter';
import { CloseIcon, SubmitIcon } from '../ui/icons';

// ── 类型 ─────────────────────────────────────────────────────

/** UI 内单个条件行（扁平化） */
interface ConditionRow {
  id: string;
  column: string;
  op: FilterOp;
  value: string;
}

/** UI 内一个组（一组条件，组间 conjunction 连接） */
interface ConditionGroup {
  id: string;
  rows: ConditionRow[];
}

/** 前端 op → 后端 op 字符串 */
const OP_MAP: Record<FilterOp, string> = {
  eq: '=',
  neq: '!=',
  gt: '>',
  ge: '>=',
  lt: '<',
  le: '<=',
  like: 'LIKE',
  not_like: 'NOT LIKE',
  in: 'IN',
  not_in: 'NOT IN',
  between: 'BETWEEN',
  text_search: 'TEXT_SEARCH',
};

const FILTER_OPS: { value: FilterOp; label: string }[] = [
  { value: 'eq', label: '=' },
  { value: 'neq', label: '!=' },
  { value: 'gt', label: '>' },
  { value: 'ge', label: '>=' },
  { value: 'lt', label: '<' },
  { value: 'le', label: '<=' },
  { value: 'like', label: '包含' },
  { value: 'not_like', label: '不包含' },
  { value: 'in', label: '包含于' },
  { value: 'not_in', label: '不包含于' },
  { value: 'between', label: '介于' },
  { value: 'text_search', label: '文本搜索' },
];

// ── DNF 序列化 / 反序列化 ─────────────────────────────────────

/** 后端 DNF 格式：[[{column, op, value}, ...], ...]
 *  外层 OR，内层 AND
 */
type DNFGroup = { column: string; op: string; value: string | number[] | string[] }[];
type DNF = DNFGroup[];

/**
 * 将 UI 显示值（逗号分隔）反序列化为 DNF value 字符串。
 * - IN / NOT IN: 数组 → JSON 数组字符串
 * - BETWEEN: [min, max] → "min,max"（逗号分隔的两个值）
 * - 其他: 原样
 */
function tryParseNumber(s: string): string | number {
  const n = Number(s);
  return !isNaN(n) && s.trim() !== '' ? n : s;
}

function serializeValue(op: FilterOp, display: string): string | number[] | string[] {
  if (op === 'in' || op === 'not_in') {
    return display
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
  }
  if (op === 'between') {
    const parts = display.split(',').map((s) => s.trim());
    if (parts.length !== 2) return '';
    return parts.map(tryParseNumber).filter((v): v is number => typeof v === 'number');
  }
  return display;
}

/**
 * 将 DNF value 字符串反序列化为 UI 显示值。
 */
function deserializeValue(op: FilterOp, raw: string | number[] | string[]): string {
  if (Array.isArray(raw)) {
    return raw.join(', ');
  }
  if (op === 'in' || op === 'not_in') {
    try {
      const arr = JSON.parse(raw);
      if (Array.isArray(arr)) return arr.join(', ');
    } catch {
      // 如果解析失败，直接返回原值
    }
    return raw;
  }
  return raw;
}

/** 从 DNF 字符串解析为 UI 分组 */
function parseDNF(json: string | null): ConditionGroup[] {
  if (!json) return [];
  try {
    const dnf: DNF = JSON.parse(json);
    return dnf.map((group) => ({
      id: genId(),
      rows: group.map((cond) => {
        // 后端 op → 前端 op
        const entry = Object.entries(OP_MAP).find(([, v]) => v === cond.op);
        const op = (entry?.[0] as FilterOp) || 'eq';
        return {
          id: genId(),
          column: cond.column,
          op,
          value: deserializeValue(op, cond.value),
        };
      }),
    }));
  } catch {
    return [];
  }
}

/** 将 UI 分组序列化为 DNF 字符串 */
function serializeDNF(groups: ConditionGroup[]): string | null {
  const valid = groups
    .map((g) => g.rows.filter((r) => r.value.trim() !== ''))
    .filter((rows) => rows.length > 0);
  if (valid.length === 0) return null;

  const dnf: DNF = valid.map((rows) =>
    rows.map((r) => ({
      column: r.column,
      op: OP_MAP[r.op],
      value: serializeValue(r.op, r.value),
    })),
  );
  return JSON.stringify(dnf);
}

// ── ValueEditor 子组件 ──────────────────────────────────────

interface ValueEditorProps {
  op: FilterOp;
  value: string;
  columnType?: string;
  onChange: (value: string) => void;
}

/** 根据运算符和列类型切换值编辑器 */
const ValueEditor: React.FC<ValueEditorProps> = ({ op, value, columnType, onChange }) => {
  // between: 两个输入框
  if (op === 'between') {
    const parts = value.split(',').map((s) => s.trim());
    const min = parts[0] || '';
    const max = parts[1] || '';

    const handleMin = (v: string) => onChange(`${v},${max}`);
    const handleMax = (v: string) => onChange(`${min},${v}`);

    return (
      <div className="flex items-center gap-1 flex-1">
        <Input
          value={min}
          onChange={(e) => handleMin(e.target.value)}
          placeholder="最小值"
          className="flex-1"
        />
        <span className="text-muted-foreground">~</span>
        <Input
          value={max}
          onChange={(e) => handleMax(e.target.value)}
          placeholder="最大值"
          className="flex-1"
        />
      </div>
    );
  }

  // in / not_in: 逗号分隔的多值输入
  if (op === 'in' || op === 'not_in') {
    return (
      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="多个值用逗号分隔"
        className="flex-1"
      />
    );
  }

  // like / not_like: 带通配符提示
  if (op === 'like' || op === 'not_like') {
    return (
      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="%通配符%"
        className="flex-1"
      />
    );
  }

  // text_search: 自动包裹 %，提示搜索关键词
  if (op === 'text_search') {
    return (
      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="搜索关键词"
        className="flex-1"
      />
    );
  }

  // 默认: 根据列类型选择合适的 input mode
  const isNumeric = columnType === 'integer' || columnType === 'float' || columnType === 'number';
  return (
    <Input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder="值"
      inputMode={isNumeric ? 'decimal' : 'text'}
      className="flex-1"
    />
  );
};

// ── 组件 ─────────────────────────────────────────────────────

interface FilterEditorProps {
  columns: { name: string; type: string }[];
  /** 初始 DNF 字符串，用于回显已有 filter */
  initialFilter?: string | null;
  onApply: (filterJson: string | null) => void;
  /** 编辑器内容变化时的回调，返回当前 DNF 字符串 */
  onChange?: (filterJson: string | null) => void;
}

export const FilterEditor: React.FC<FilterEditorProps> = ({
  columns,
  initialFilter,
  onApply,
  onChange,
}) => {
  const [groups, setGroups] = useState<ConditionGroup[]>(() => {
    const parsed = parseDNF(initialFilter ?? null);
    return parsed.length > 0 ? parsed : [];
  });

  // 同步 DNF 到父组件
  useEffect(() => {
    onChange?.(serializeDNF(groups));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [groups]);

  // ── 组操作 ──────────────────────────────────────────────

  const addGroup = () => {
    setGroups((prev) => [
      ...prev,
      { id: genId(), rows: [{ id: genId(), column: columns[0]?.name || '', op: 'eq' as FilterOp, value: '' }] },
    ]);
  };

  const removeGroup = (gid: string) => {
    setGroups((prev) => prev.filter((g) => g.id !== gid));
  };

  // ── 行操作 ──────────────────────────────────────────────

  const addRow = (gid: string) => {
    setGroups((prev) =>
      prev.map((g) =>
        g.id === gid
          ? {
              ...g,
              rows: [
                ...g.rows,
                { id: genId(), column: columns[0]?.name || '', op: 'eq' as FilterOp, value: '' },
              ],
            }
          : g,
      ),
    );
  };

  const updateRow = (gid: string, rid: string, patch: Partial<ConditionRow>) => {
    setGroups((prev) =>
      prev.map((g) =>
        g.id === gid
          ? {
              ...g,
              rows: g.rows.map((r) => (r.id === rid ? { ...r, ...patch } : r)),
            }
          : g,
      ),
    );
  };

  const removeRow = (gid: string, rid: string) => {
    setGroups((prev) =>
      prev
        .map((g) => ({
          ...g,
          rows: g.rows.filter((r) => r.id !== rid),
        }))
        .filter((g) => g.rows.length > 0),
    );
  };

  // ── 应用 / 清除 ─────────────────────────────────────────

  const handleApply = () => {
    onApply(serializeDNF(groups));
  };

  const handleClear = () => {
    setGroups([]);
  };

  // ── 分组间连接词 ─────────────────────────────────────────

  const isFirstGroup = (idx: number) => idx === 0;

  return (
    <Card className="mb-4">
      <CardContent className="p-4 space-y-4">
        {/* 标题 + 操作按钮 */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">筛选条件</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={addGroup}>
              + OR 组
            </Button>
            <Button variant="ghost" size="sm" onClick={handleClear} title="清除">
              <CloseIcon/>
            </Button>
            <Button size="sm" onClick={handleApply} title="提交">
              <SubmitIcon/>
            </Button>
          </div>
        </div>

        {/* 分组列表 */}
        {groups.map((group, gi) => (
          <div key={group.id} className="space-y-2">
            {/* OR 分隔线 */}
            {!isFirstGroup(gi) && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <div className="flex-1 border-t" />
                <span className="font-semibold text-orange-500">OR</span>
                <div className="flex-1 border-t" />
              </div>
            )}

            {/* 组头 */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                AND 组 {gi + 1}
              </span>
              <div className="flex gap-1">
                <Button variant="ghost" size="sm" onClick={() => addRow(group.id)}>
                  + 条件
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeGroup(group.id)}
                  className="text-destructive"
                >
                  删除组
                </Button>
              </div>
            </div>

            {/* 条件行 */}
            {group.rows.map((row) => (
              <div key={row.id} className="flex items-center gap-2">
                <Select
                  value={row.column}
                  onChange={(e) => updateRow(group.id, row.id, { column: e.target.value })}
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
                  onChange={(e) => {
                    // 切换运算符时清空值，避免格式冲突
                    updateRow(group.id, row.id, { op: e.target.value as FilterOp, value: '' });
                  }}
                  className="w-24"
                >
                  {FILTER_OPS.map((op) => (
                    <option key={op.value} value={op.value}>
                      {op.label}
                    </option>
                  ))}
                </Select>

                <ValueEditor
                  op={row.op}
                  value={row.value}
                  columnType={columns.find((c) => c.name === row.column)?.type}
                  onChange={(val) => updateRow(group.id, row.id, { value: val })}
                />

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeRow(group.id, row.id)}
                  className="text-destructive"
                >
                  ×
                </Button>
              </div>
            ))}
          </div>
        ))}

        {/* 空状态 */}
        {groups.length === 0 && (
          <p className="text-xs text-muted-foreground">
            点击"OR 组"添加一组条件，同一组内条件为 AND 关系
          </p>
        )}
      </CardContent>
    </Card>
  );
};
