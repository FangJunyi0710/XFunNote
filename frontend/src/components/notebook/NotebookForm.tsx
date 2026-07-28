import React, { useState, useEffect, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { ColumnDef, NotebookSchema } from '@/types/notebook';
import { ReplyIcon, SubmitIcon } from '@/components/ui/icons';
import { ChevronRightIcon, ChevronUpIcon } from '@/components/ui/icons';
import { COLUMN_RENDERER_TYPES, getFieldLabel, toDisplay, toStorage, FIELD_TRANSFORMS } from "@/config/notebook";

// ---------------------------------------------------------------------------
// 注册表：按 col.type 分发渲染器
// ---------------------------------------------------------------------------
type FieldRenderer = (
  col: ColumnDef,
  value: unknown,
  onChange: (v: unknown) => void,
  disableRequired: boolean,
) => React.ReactNode;

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

/** 带转换的输入框组件：保留本地输入状态，避免实时格式化 */
// 新建一个组件，在组件内部使用 Hook
const InputWithTransform: React.FC<{
  col: ColumnDef;
  value: unknown;
  onChange: (v: unknown) => void;
  disableRequired: boolean;
  type: string;
  step?: string | undefined;
}> = ({ col, value, onChange, disableRequired, type, step }) => {
  const [inputValue, setInputValue] = useState(() => {
    const displayed = toDisplay(col.name, value);
    return displayed !== null && displayed !== undefined ? String(displayed) : '';
  });

  useEffect(() => {
    const displayed = toDisplay(col.name, value);
    const newVal = displayed !== null && displayed !== undefined ? String(displayed) : '';
    setInputValue(newVal);
  }, [col.name, value]);

  const handleBlur = () => {
    const storage = toStorage(col.name, inputValue);
    onChange(storage);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  return (
    <div key={col.name} className="space-y-1">
      <FieldLabel name={col.name} required={col.required} />
      <Input
        type={type}
        step={step ?? undefined}
        value={inputValue}
        onChange={handleChange}
        onBlur={handleBlur}
        required={!disableRequired && col.required}
        placeholder="输入内容..."
      />
    </div>
  );
};

const createInputRenderer = (type?: string, step?: string): FieldRenderer => 
  (col, value, onChange, disableRequired) => (
    <InputWithTransform
      key={col.name}
      col={col}
      value={value}
      onChange={onChange}
      disableRequired={disableRequired}
      type={type ?? 'text'}
      step={step}
    />
  );

const renderTextareaField: FieldRenderer = (col, value, onChange, disableRequired) => (
  <div key={col.name} className="space-y-1">
    <FieldLabel name={col.name} required={col.required} />
    <Textarea
      value={value as string}
      onChange={(e) => onChange(e.target.value)}
      rows={col.name === 'content' ? 4 : 2}
      required={!disableRequired && col.required}
      placeholder="输入内容..."
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
    <div key={col.name} className="space-y-1">
      <FieldLabel name={col.name} required={col.required} />
      <div className="flex items-center gap-2">
        <Checkbox
          id={col.name}
          checked={checked}
          onCheckedChange={(v) => handleChange(v)}
        />
        <label htmlFor={col.name} className="text-sm font-medium">
          {toDisplay(col.name, value) as string}
        </label>
      </div>
    </div>
  );
};

/** 选择器字段（用于 state 等枚举字段） */
const renderSelectField: FieldRenderer = (col, value, onChange, disableRequired) => {
  const transform = FIELD_TRANSFORMS[col.name];
  if (!transform?.options) {
    return createInputRenderer()(col, value, onChange, disableRequired);
  }
  const currentDisplay = toDisplay(col.name, value) as string;
  return (
    <div key={col.name} className="space-y-1">
      <FieldLabel name={col.name} required={col.required} />
      <select
        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        value={currentDisplay}
        onChange={(e) => {
          const display = e.target.value;
          if (display === '') {
            onChange(null);
            return;
          }
          const storage = toStorage(col.name, display);
          onChange(storage);
        }}
        required={!disableRequired && col.required}
      >
        <option value="">未选择</option>
        {Object.entries(transform.options).map(([storage, display]) => (
          <option key={storage} value={display}>
            {display}
          </option>
        ))}
      </select>
    </div>
  );
};


/** 类型名 → 渲染器映射 */
const typeRenderers: Record<string, FieldRenderer> = {
  TEXT: createInputRenderer(),
  INTEGER: createInputRenderer('number', '1'),
  REAL: createInputRenderer('number', 'any'),
  Textarea: renderTextareaField,
  Boolean: renderBooleanField,
  Date: createInputRenderer('date'),
  DateTime: createInputRenderer('datetime-local'),
  Select: renderSelectField,
};

// ---------------------------------------------------------------------------
// 组件
// ---------------------------------------------------------------------------
interface NotebookFormProps {
  schema: NotebookSchema;
  initialData?: Record<string, unknown> | undefined;
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
    const renderer = typeRenderers[COLUMN_RENDERER_TYPES[col.name] || col.type] || createInputRenderer();
    return renderer(col, value, onChange, disableRequired ?? false);
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
