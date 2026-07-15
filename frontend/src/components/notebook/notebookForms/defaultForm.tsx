import React, { useState, useEffect, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { ColumnDef, NotebookSchema } from '@/types/notebook';

// ---------------------------------------------------------------------------
// 注册表：按 col.type 分发渲染器
// ---------------------------------------------------------------------------
type FieldRenderer = (
  col: ColumnDef,
  value: unknown,
  onChange: (v: unknown) => void,
  disableRequired?: boolean,
) => React.ReactNode;

/** 带红色 * 的标签 */
const FieldLabel: React.FC<{ name: string; required?: boolean }> = ({
  name,
  required,
}) => (
  <label className="text-sm font-medium">
    {name}
    {required && <span className="ml-0.5 text-destructive">*</span>}
  </label>
);

const renderTextField: FieldRenderer = (col, value, onChange, disableRequired) => (
  <div key={col.name} className="space-y-1">
    <FieldLabel name={col.name} required={col.required} />
    <Input
      value={value as string}
      onChange={(e) => onChange(e.target.value)}
      required={!disableRequired && col.required}
      placeholder={col.name}
    />
  </div>
);

const renderTextareaField: FieldRenderer = (col, value, onChange, disableRequired) => (
  <div key={col.name} className="space-y-1">
    <FieldLabel name={col.name} required={col.required} />
    <Textarea
      value={value as string}
      onChange={(e) => onChange(e.target.value)}
      rows={col.name === 'content' ? 4 : 2}
      required={!disableRequired && col.required}
    />
  </div>
);

/** 布尔 / done(0/1) 字段渲染为复选框 */
const renderBooleanField: FieldRenderer = (col, value, onChange) => {
  // done 是 INTEGER(0/1)，需要做类型转换
  const isDone = col.name === 'done';
  const checked = isDone ? value === 1 || value === true : !!value;
  const handleChange = (v: boolean) => {
    onChange(isDone ? (v ? 1 : 0) : v);
  };
  return (
    <div key={col.name} className="flex items-center gap-2">
      <Checkbox
        id={col.name}
        checked={checked}
        onChange={(e) => handleChange(e.target.checked)}
      />
      <label htmlFor={col.name} className="text-sm font-medium">
        {col.name}
      </label>
    </div>
  );
};

/** 按列名和类型查找渲染器的注册表 */
const FIELD_RENDERERS: Record<string, FieldRenderer> = {
  boolean: renderBooleanField,
  text: renderTextareaField,
  done: renderBooleanField,   // done 是 0/1 整数，但语义是布尔值，渲染为复选框
};

// ---------------------------------------------------------------------------
// 组件
// ---------------------------------------------------------------------------
interface NotebookFormProps {
  schema: NotebookSchema;
  initialData?: Record<string, unknown>;
  onSubmit: (data: Record<string, unknown>) => Promise<void>;
  onCancel: () => void;
  title?: string;
  /** 关闭原生 required 校验（批量更新时使用） */
  disableRequired?: boolean;
}

export const NotebookForm: React.FC<NotebookFormProps> = ({
  schema,
  initialData,
  onSubmit,
  onCancel,
  title,
  disableRequired,
}) => {
  const [formData, setFormData] = useState<Record<string, unknown>>({});
  const [submitting, setSubmitting] = useState(false);

  // 自动填充/内部字段，不应展示给用户
  const AUTO_FIELDS = useMemo(
    () => new Set(['id', 'created_at', 'updated_at', 'is_ai_gen', 'ai_tags', 'ai_note', 'tags', 'no', 'seq', 'review_count', 'performance']),
    [],
  );

  useEffect(() => {
    if (initialData) {
      setFormData({ ...initialData });
    } else {
      const defaults: Record<string, unknown> = {};
      schema.columns.forEach((col) => {
        if (AUTO_FIELDS.has(col.name)) return;
        defaults[col.name] = col.default !== undefined ? col.default : '';
      });
      setFormData(defaults);
    }
  }, [initialData, schema, AUTO_FIELDS]);

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
    if (AUTO_FIELDS.has(col.name)) return null;

    const value = formData[col.name] ?? '';
    const onChange = (v: unknown) => handleChange(col.name, v);

    // 按类型查找渲染器，特殊列名兜底
    const renderer =
      FIELD_RENDERERS[col.name] ??
      FIELD_RENDERERS[col.type] ??
      renderTextField;

    return renderer(col, value, onChange, disableRequired);
  };

  const editableColumns = useMemo(
    () => schema.columns.filter((c) => !AUTO_FIELDS.has(c.name)),
    [schema, AUTO_FIELDS],
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title || (initialData ? '编辑条目' : '新建条目')}</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {editableColumns.map(renderField)}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onCancel}>
              取消
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? '提交中...' : '提交'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};
