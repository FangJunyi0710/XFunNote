import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { ColumnDef, NotebookSchema } from '@/types/notebook';
import { ReplyIcon, SubmitIcon } from '@/components/ui/icons';
import { ChevronRightIcon, ChevronUpIcon } from '@/components/ui/icons';

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

/** 日期/时间字段渲染为原生日期时间选择器 */
const renderDateTimeField: FieldRenderer = (col, value, onChange, disableRequired) => {
  // 判断使用 date 还是 datetime-local
  const isDateOnly = ['date', 'next_review', 'last_review'].includes(col.name);
  const inputType = isDateOnly ? 'date' : 'datetime-local';

  // 将后端日期字符串转换为输入框所需格式
  const formatValue = (val: unknown): string => {
    if (!val) return '';
    const d = typeof val === 'string' ? new Date(val) : val;
    if (d instanceof Date && !isNaN(d.getTime())) {
      if (isDateOnly) {
        return d.toISOString().split('T')[0];
      }
      // datetime-local: YYYY-MM-DDTHH:mm
      return d.toISOString().slice(0, 16);
    }
    return '';
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    if (!raw) {
      onChange(null);
      return;
    }
    if (isDateOnly) {
      // date: 转为 UTC 日期字符串 (YYYY-MM-DD)
      onChange(raw);
    } else {
      // datetime-local: 转为 ISO 字符串
      const d = new Date(raw);
      if (!isNaN(d.getTime())) {
        onChange(d.toISOString());
      }
    }
  };

  return (
    <div key={col.name} className="space-y-1">
      <FieldLabel name={col.name} required={col.required} />
      <Input
        type={inputType}
        value={formatValue(value)}
        onChange={handleChange}
        required={!disableRequired && col.required}
      />
    </div>
  );
};

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
        onCheckedChange={(v) => handleChange(v)}
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
  date: renderDateTimeField,
  datetime: renderDateTimeField,
  done: renderBooleanField,
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
  const [autoFieldsCollapsed, setAutoFieldsCollapsed] = useState(true);

  // 自动字段集合（使用 ref 缓存，避免因引用变化触发重渲染）
  const autoFieldNamesRef = useRef<Set<string>>(new Set());
  const prevColumnsKeyRef = useRef<string>('');

  // 仅在 schema.columns 实际内容变化时更新 autoFieldNamesRef
  useEffect(() => {
    const key = schema.columns.map(c => c.name + '|' + c.auto).join(',');
    if (prevColumnsKeyRef.current !== key) {
      prevColumnsKeyRef.current = key;
      autoFieldNamesRef.current = new Set(
        schema.columns.filter((c) => c.auto === true).map((c) => c.name)
      );
    }
  }, [schema.columns]);

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
    } else {
      const defaults: Record<string, unknown> = {};
      schema.columns.forEach((col) => {
        if (autoFieldNamesRef.current.has(col.name)) return;
        defaults[col.name] = col.default !== undefined ? col.default : '';
      });
      setFormData((prev) => {
        // 防止重复设置相同默认值
        if (Object.keys(prev).length === Object.keys(defaults).length &&
            Object.keys(prev).every(k => prev[k] === defaults[k])) {
          return prev;
        }
        return defaults;
      });
    }
  }, [initialData, schema.columns]);

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

    const renderer = FIELD_RENDERERS[col.name] ?? FIELD_RENDERERS[col.type] ?? renderTextField;
    return renderer(col, value, onChange, disableRequired);
  };


  return (
    <Card>
      <form onSubmit={handleSubmit}>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>{title || (initialData ? '编辑条目' : '新建条目')}</span>
            <span className="flex gap-2">
              <Button type="button" variant="outline" onClick={onCancel} title="返回">
                <ReplyIcon/>
              </Button>
              <Button type="submit" disabled={submitting} title="提交">
                <SubmitIcon/>
              </Button>
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 可编辑字段 */}
          {schema.columns.filter((c) => !autoFieldNamesRef.current.has(c.name)).map((col) => renderField(col))}

          {/* 自动字段折叠面板 */}
          {(() => {
            const autoCols = schema.columns.filter((c) => autoFieldNamesRef.current.has(c.name));
            if (autoCols.length === 0) return null;
            return (
              <div className="mt-4 pt-4 border-t border-border/50">
                <button
                  type="button"
                  onClick={() => setAutoFieldsCollapsed(!autoFieldsCollapsed)}
                  className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors mb-3"
                >
                  <span>{autoFieldsCollapsed ? <ChevronRightIcon size={12} className="inline-block" /> : <ChevronUpIcon size={12} className="inline-block -rotate-180" />}</span>
                  <span>系统自动字段（{autoCols.length} 个）</span>
                  <span className="text-[10px] text-muted-foreground/60">不建议手动修改</span>
                </button>
                {!autoFieldsCollapsed && autoCols.map((col) => renderField(col))}
              </div>
            );
          })()}
        </CardContent>
      </form>
    </Card>
  );
};
