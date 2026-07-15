import React, { useState, useMemo, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { genId } from '@/lib/utils';
import type { FilterOp } from '@/types/filter';

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
  in: 'IN',
};

const FILTER_OPS: { value: FilterOp; label: string }[] = [
  { value: 'eq', label: '=' },
  { value: 'neq', label: '!=' },
  { value: 'gt', label: '>' },
  { value: 'ge', label: '>=' },
  { value: 'lt', label: '<' },
  { value: 'le', label: '<=' },
  { value: 'like', label: '包含' },
];

// ── DNF 序列化 / 反序列化 ─────────────────────────────────────

/** 后端 DNF 格式：[[{column, op, value}, ...], ...]
 *  外层 OR，内层 AND
 */
type DNFGroup = { column: string; op: string; value: string }[];
type DNF = DNFGroup[];

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
        return {
          id: genId(),
          column: cond.column,
          op: (entry?.[0] as FilterOp) || 'eq',
          value: cond.value,
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
      value: r.value,
    })),
  );
  return JSON.stringify(dnf);
}

// ── 组件 ─────────────────────────────────────────────────────

interface FilterEditorProps {
  columns: { name: string; type: string }[];
  /** 初始 DNF 字符串，用于回显已有 filter */
  initialFilter?: string | null;
  onApply: (filterJson: string | null) => void;
  /** 编辑器内容变化时的回调，返回当前 DNF 字符串 */
  onChange?: (filterJson: string | null) => void;
  onCancel?: () => void;
}

export const FilterEditor: React.FC<FilterEditorProps> = ({
  columns,
  initialFilter,
  onApply,
  onChange,
  onCancel,
}) => {
  const [groups, setGroups] = useState<ConditionGroup[]>(() => {
    const parsed = parseDNF(initialFilter);
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

  const updateRow = (gid: string, rid: string, field: keyof ConditionRow, val: string) => {
    setGroups((prev) =>
      prev.map((g) =>
        g.id === gid
          ? {
              ...g,
              rows: g.rows.map((r) => (r.id === rid ? { ...r, [field]: val } : r)),
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
    onApply(null);
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
            {groups.length > 0 && (
              <>
                <Button variant="ghost" size="sm" onClick={handleClear}>
                  清除
                </Button>
                <Button size="sm" onClick={handleApply}>
                  应用
                </Button>
              </>
            )}
            {onCancel && (
              <Button variant="ghost" size="sm" onClick={onCancel}>
                取消
              </Button>
            )}
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
                  onChange={(e) => updateRow(group.id, row.id, 'column', e.target.value)}
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
                  onChange={(e) => updateRow(group.id, row.id, 'op', e.target.value)}
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
                  onChange={(e) => updateRow(group.id, row.id, 'value', e.target.value)}
                  placeholder="值"
                  className="flex-1"
                />

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeRow(group.id, row.id)}
                  className="text-destructive"
                >
                  ✕
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
