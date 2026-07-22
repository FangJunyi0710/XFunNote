import React, { useState, useEffect, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { ColumnDef, NotebookSchema } from '@/types/notebook';
import { ReplyIcon, SubmitIcon } from '@/components/ui/icons';
import { ChevronRightIcon, ChevronUpIcon } from '@/components/ui/icons';
import { COLUMN_RENDERER_TYPES } from "@/config/notebook";

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

/** 日期字段渲染为原生 date 选择器 */
const renderDateField: FieldRenderer = (col, value, onChange, disableRequired) => {
  // 将后端日期字符串转换为输入框所需格式 (YYYY-MM-DD)
  const formatValue = (val: unknown): string => {
    if (!val) return '';
    const d = typeof val === 'string' ? new Date(val) : val;
    if (d instanceof Date && !isNaN(d.getTime())) {
      // date: YYYY-MM-DD
      return d.toISOString().split('T')[0];
    }
    return '';
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    if (!raw) {
      onChange(null);
      return;
    }
    // date: 直接传递 YYYY-MM-DD
    onChange(raw);
  };

  return (
    <div key={col.name} className="space-y-1">
      <FieldLabel name={col.name} required={col.required} />
      <Input
        type="date"
        value={formatValue(value)}
        onChange={handleChange}
        required={!disableRequired && col.required}
      />
    </div>
  );
};

/** 日期时间字段渲染为原生 datetime-local 选择器 */
const renderDateTimeField: FieldRenderer = (col, value, onChange, disableRequired) => {
  // 将存储的 UTC 时间转为本地时间字符串用于显示（格式：YYYY-MM-DDTHH:mm）
  const formatValue = (val: unknown): string => {
    if (!val) return '';
    const d = typeof val === 'string' ? new Date(val) : val;
    if (d instanceof Date && !isNaN(d.getTime())) {
      const year = d.getFullYear();
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      const hours = String(d.getHours()).padStart(2, '0');
      const minutes = String(d.getMinutes()).padStart(2, '0');
      return `${year}-${month}-${day}T${hours}:${minutes}`;
    }
    return '';
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    if (!raw) {
      onChange(null);
      return;
    }
    const d = new Date(raw);
    if (!isNaN(d.getTime())) {
      onChange(d.toISOString());
    }
  };

  return (
    <div key={col.name} className="space-y-1">
      <FieldLabel name={col.name} required={col.required} />
      <Input
        type="datetime-local"
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
/** 布尔 字段渲染为复选框 */
const renderBooleanField: FieldRenderer = (col, value, onChange) => {
  const checked = value === 1 || value === true;
  const handleChange = (v: boolean) => {
    onChange(v ? 1 : 0);
  };
  return (
    <div key={col.name} className="flex items-center gap-2">
      <label htmlFor={col.name} className="text-sm font-medium">
        {col.name}
      </label>
      <Checkbox
        id={col.name}
        checked={checked}
        onCheckedChange={(v) => handleChange(v)}
      />
    </div>
  );
};

const createNumberRenderer = (step?: string): FieldRenderer => 
  (col, value, onChange, disableRequired) => (
    <div key={col.name} className="space-y-1">
      <FieldLabel name={col.name} required={col.required} />
      <Input
        type="number"
        step={step}
        value={value as number ?? ''}
        onChange={(e) => onChange(e.target.value === '' ? null : Number(e.target.value))}
        required={!disableRequired && col.required}
        placeholder={col.name}
      />
    </div>
  );


/** 类型名 → 渲染器映射 */
const typeRenderers: Record<string, FieldRenderer> = {
  TEXT: renderTextField,
  INTEGER: createNumberRenderer("1"),
  REAL: createNumberRenderer("any"),
  Textarea: renderTextareaField,
  Boolean: renderBooleanField,
  Date: renderDateField,
  DateTime: renderDateTimeField,
};
// TODO 下一步：做字段名与值的双向自动转换优化用户体验


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

  const autoFieldNames = useMemo(() => new Set(schema.columns.filter((c) => c.auto === true).map((c) => c.name)), [schema.columns]);

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
        if (autoFieldNames.has(col.name)) return;
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
  }, [initialData]);

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
    const renderer = typeRenderers[COLUMN_RENDERER_TYPES[col.name] || col.type] || renderTextField;
    return renderer(col, value, onChange, disableRequired);
  };

  return (
    <Card>
      <form onSubmit={handleSubmit}>
        <CardHeader className="sticky top-0 z-10 bg-background/95 backdrop-blur-sm border-b border-border/50 pb-2">
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
        <CardContent>
          {/* 可编辑字段 */}
          {schema.columns.filter((c) => !autoFieldNames.has(c.name)).map((col) => renderField(col))}

          {/* 自动字段折叠面板 */}
          {(() => {
            const autoCols = schema.columns.filter((c) => autoFieldNames.has(c.name));
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
