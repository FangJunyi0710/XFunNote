import { useEffect, useState } from "react";
import type { ColumnDef } from "@/types/notebook";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { COLUMN_TYPES, FIELD_TRANSFORMS, toDisplay, toStorage } from "@/config/notebook";


// ---------------------------------------------------------------------------
// 注册表：按 col.type 分发渲染器
// ---------------------------------------------------------------------------

type ValueEditorComponent = React.FC<({
  col: ColumnDef;
  value: unknown;
  onChange: (v: unknown) => void;
  enableRequired?: boolean | undefined;
})>;

/** 带转换的输入框组件：保留本地输入状态，避免实时格式化 */
// 新建一个组件，在组件内部使用 Hook
const InputWithTransform: React.FC<{
  col: ColumnDef;
  value: unknown;
  onChange: (v: unknown) => void;
  enableRequired?: boolean | undefined;
  type: string;
  step?: string | undefined;
}> = ({ col, value, onChange, enableRequired, type, step }) => {
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

  return <Input
    type={type}
    step={step ?? undefined}
    value={inputValue}
    onChange={handleChange}
    onBlur={handleBlur}
    required={enableRequired && col.required}
    placeholder="输入内容..."
  />;
};

const createInputRenderer = (type?: string, step?: string): ValueEditorComponent => {
  return ({ col, value, onChange, enableRequired }) => (
    <InputWithTransform
      key={col.name}
      col={col}
      value={value}
      onChange={onChange}
      enableRequired={enableRequired}
      type={type ?? 'text'}
      step={step}
    />
  );
};

const renderTextareaField: ValueEditorComponent = ({col, value, onChange, enableRequired}) => (
  <Textarea
    value={value as string}
    onChange={(e) => onChange(e.target.value)}
    rows={col.name === 'content' ? 4 : 2}
    required={enableRequired && col.required}
    placeholder="输入内容..."
  />
);
/** 布尔 字段渲染为复选框 */
const renderBooleanField: ValueEditorComponent = ({col, value, onChange}) => {
  const checked = value === 1 || value === true;
  const handleChange = (v: boolean) => {
    onChange(v ? 1 : 0);
  };
  return <div className="flex items-center gap-2">
    <Checkbox
      id={col.name}
      checked={checked}
      onCheckedChange={(v) => handleChange(v)}
    />
    <label htmlFor={col.name} className="text-sm font-medium">
      {toDisplay(col.name, value) as string}
    </label>
  </div>;
};

/** 选择器字段（用于 state 等枚举字段） */
const renderSelectField: ValueEditorComponent = ({col, value, onChange, enableRequired}) => {
  const transform = FIELD_TRANSFORMS[col.name];
  if (!transform?.options) {
    return createInputRenderer()({col, value, onChange, enableRequired});
  }
  const currentDisplay = toDisplay(col.name, value) as string;
  return <select
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
    required={enableRequired && col.required}
  >
    <option value="">未选择</option>
    {Object.entries(transform.options).map(([storage, display]) => (
      <option key={storage} value={display}>
        {display}
      </option>
    ))}
  </select>;
};


/** 类型名 → 渲染器映射 */
const typeRenderers: Record<string, ValueEditorComponent> = {
  TEXT: createInputRenderer(),
  INTEGER: createInputRenderer('number', '1'),
  REAL: createInputRenderer('number', 'any'),
  Textarea: renderTextareaField,
  Boolean: renderBooleanField,
  Date: createInputRenderer('date'),
  DateTime: createInputRenderer('datetime-local'),
  Select: renderSelectField,
};

export const ValueEditor: ValueEditorComponent = ({col, value, onChange, enableRequired}) => {
  const Editor = typeRenderers[COLUMN_TYPES[col.name] || col.type] || createInputRenderer();
  return Editor({col, value, onChange, enableRequired});
}
