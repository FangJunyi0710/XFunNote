import React, { useState, useEffect, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { ColumnDef, NotebookSchema } from '@/types/notebook';
import { ArrowIcon, ReplyIcon, SubmitIcon } from '@/components/ui/icons';
import { getFieldDefault, getFieldLabel, sortColumns } from "@/config/notebook";
import { ValueEditor } from '@/components/notebook/ValueEditor';

// ---------------------------------------------------------------------------
// 组件
// ---------------------------------------------------------------------------

/** 带红色 * 的标签 */
const FieldLabel: React.FC<{ name: string; required?: boolean }> = ({
  name,
  required,
}) => (
  <label className="text-base font-medium">
    {getFieldLabel(name)}
    {required && <span className="ml-0.5 text-destructive">*</span>}
  </label>
);

export const NotebookForm: React.FC<{
  schema: NotebookSchema;
  initialData?: Record<string, unknown> | null;
  onSubmit: (data: Record<string, unknown>) => Promise<void>;
  onCancel: () => void;
  title?: string;
  /** 关闭原生 required 校验（批量更新时使用） */
  disableRequired?: boolean;
}> = ({
  schema,
  initialData,
  onSubmit,
  onCancel,
  title,
  disableRequired,
}) => {
  const [formData, setFormData] = useState<Record<string, unknown>>({});
  const [submitting, setSubmitting] = useState(false);
  const [autoFieldsCollapsed, setAutoFieldsCollapsed] = useState(true);

  const autoFieldNames = useMemo(() => new Set(schema.columns.filter((c) => c.auto === true).map((c) => c.name)), [schema.columns]);

  const sortedColumns = useMemo(() => sortColumns(schema.columns), [schema.columns]);

  useEffect(() => {
    if (initialData) {
      setFormData((prev) => {
        // 防止重复设置相同数据
        if (Object.keys(prev).length === Object.keys(initialData).length &&
            Object.keys(prev).every(k => prev[k] === initialData[k])) {
          return prev;
        }
        return { ...initialData };
      });
    } else if (!disableRequired) {
      // 新建模式：自动填充默认值（跳过 auto 字段）
      const defaults: Record<string, unknown> = {};
      schema.columns.forEach(col => {
        if (col.auto) return; // 后端自动生成的字段不预填
        const val = getFieldDefault(col.name);
        if (val !== null && val !== undefined) {
          defaults[col.name] = val;
        }
      });
      setFormData((prev) => {
        // 如果已有数据（如页面复用时），不覆盖
        if (Object.keys(prev).length > 0) return prev;
        return defaults;
      });
    } else {
      // 批量更新模式：不自动填充
      setFormData({});
    }
  }, [initialData, schema, disableRequired]);

  const handleChange = (name: string, value: unknown) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit(formData);
    } finally {
      setSubmitting(false);
    }
  };

  const renderField = (col: ColumnDef) => {
    const value = formData[col.name] ?? '';
    const onChange = (v: unknown) => handleChange(col.name, v);
    return <div key={col.name} className="space-y-1">
      <FieldLabel name={col.name} required={!disableRequired && col.required} />
      <ValueEditor col={col} value={value} onChange={onChange}
        required={!disableRequired && col.required}
        placeholder={initialData ? '编辑内容' : disableRequired ? '修改字段' : '输入内容'}
      />
    </div>;
  };

  return (
    <Card>
      <form onSubmit={handleSubmit}>
        <CardHeader className="sticky top-0 z-10 bg-background/95 backdrop-blur-sm border-b border-border/50 pb-2">
          <CardTitle className="flex items-center justify-between">
            <span>{title || (initialData ? '编辑条目' : '新建条目')}</span>
            <span className="flex gap-2">
              <Button variant="outline" onClick={onCancel} title="返回">
                <ReplyIcon/>
              </Button>
              <Button type="submit" disabled={submitting} title="提交">
                <SubmitIcon/>
              </Button>
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* 可编辑字段 */}
          {sortedColumns.filter((c) => !autoFieldNames.has(c.name)).map((col) => renderField(col))}

          {/* 自动字段折叠面板 */}
          {(() => {
            const autoCols = sortedColumns.filter((c) => autoFieldNames.has(c.name));
            if (autoCols.length === 0) return null;
            return (
              <div className="mt-4 pt-4 border-t border-border/50">
                <Button
                  onClick={() => setAutoFieldsCollapsed(!autoFieldsCollapsed)}
                  className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors mb-3"
                >
                  <span>{autoFieldsCollapsed ? <ArrowIcon direction='right' size={12} className="inline-block" /> : <ArrowIcon direction='down' size={12} className="inline-block -rotate-180" />}</span>
                  <span>系统自动字段（{autoCols.length} 个）</span>
                  <span className="text-[10px] text-muted-foreground/60">不建议手动修改</span>
                </Button>
                {!autoFieldsCollapsed && autoCols.map((col) => renderField(col))}
              </div>
            );
          })()}
        </CardContent>
      </form>
    </Card>
  );
};
// TODO 前端编辑条目提供更合适的文本框，带记忆功能
// TODO 前端表单将大部分信息自动填充
// TODO 表单允许填空值
// TODO 批量更新改为可以清空某些字段：使用复选框明确所更新项
