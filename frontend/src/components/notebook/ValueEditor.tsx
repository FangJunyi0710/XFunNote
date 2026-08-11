import { useEffect, useState } from "react";
import type { ColumnDef } from "@/types/notebook";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { FIELD_TRANSFORMS, getColumnType, toDisplay, toStorage } from "@/config/notebook";
import { cn } from "@/lib/utils";


// ---------------------------------------------------------------------------
// 注册表：按 col.type 分发渲染器
// ---------------------------------------------------------------------------

type ValueEditorComponent = React.FC<{
  col: ColumnDef;
  value: unknown;
  onChange: (v: unknown) => void;
  [key: string]: unknown;
}>;

/** 带转换的输入框组件：保留本地输入状态，避免实时格式化 */
// 新建一个组件，在组件内部使用 Hook
const InputWithTransform: React.FC<{
  col: ColumnDef;
  value: unknown;
  onChange: (v: unknown) => void;
  type: string;
}> = ({ col, value, onChange, type, ...props }) => {
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
    key={col.name}
    type={type}
    value={inputValue}
    onChange={handleChange}
    onBlur={handleBlur}
    {...props}
  />;
};

const createInputRenderer = (type?: string, extras?: Record<string, unknown>): ValueEditorComponent => {
  return ({ col, value, onChange, ...props }) => (
    <InputWithTransform
      key={col.name}
      col={col}
      value={value}
      onChange={onChange}
      type={type ?? 'text'}
      {...extras}
      {...props}
    />
  );
};

const renderTextareaField: ValueEditorComponent = ({col, value, onChange, ...props}) => {
  const [inputText, setInputText] = useState<string>((value ?? '') as string);
  return <Textarea
    key={col.name}
    value={inputText}
    onChange={e => setInputText(e.target.value)}
    onBlur={() => onChange(inputText)}
    {...props}
  />
};
/** 布尔 字段渲染为复选框 */
const renderBooleanField: ValueEditorComponent = ({col, value, onChange, ...props}) => {
  const handleChange = (v: boolean) => {
    onChange(v ? 1 : 0);
  };
  useEffect(() => {
    if (typeof value !== 'number' || value !== 0 && value !== 1) {
      handleChange(Boolean(value));
    }
  }, []);
  const id = `checkbox-${col.name}`;
  return <div className="flex items-center gap-2">
    <Checkbox
      id={id}
      key={col.name}
      checked={Boolean(value)}
      onCheckedChange={v => handleChange(v)}
      {...props}
    />
    <label htmlFor={id} className="text-sm font-medium">
      {toDisplay(col.name, value) as string}
    </label>
  </div>;
};

/** 选择器字段（用于 state 等枚举字段） */
const renderSelectField: ValueEditorComponent = ({col, value, onChange, ...props}) => {
  const transform = FIELD_TRANSFORMS[col.name];
  if (!transform?.options) {
    return createInputRenderer()({col, value, onChange, ...props});
  }
  const currentDisplay = toDisplay(col.name, value) as string;
  return <select
    key={col.name}
    className={cn('w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2', props["className"] as string | undefined)}
    value={currentDisplay}
    onChange={e => {
      const display = e.target.value;
      if (display === '') {
        onChange(null);
        return;
      }
      const storage = toStorage(col.name, display);
      onChange(storage);
    }}
    {...props}
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
  INTEGER: createInputRenderer('number', {step: '1'}),
  REAL: createInputRenderer('number', {step: 'any'}),
  Textarea: renderTextareaField,
  Boolean: renderBooleanField,
  Date: createInputRenderer('date'),
  DateTime: createInputRenderer('datetime-local'),
  Select: renderSelectField,
};

export const ValueEditor: ValueEditorComponent = ({col, value, onChange, ...props}) => {
  const Editor = typeRenderers[getColumnType(col)] || createInputRenderer();
  return <Editor col={col} value={value} onChange={onChange} {...props} />;
}
