import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { NotebookSchema } from '@/types/notebook';

interface NotebookFormProps {
  schema: NotebookSchema;
  initialData?: Record<string, any>;
  onSubmit: (data: Record<string, any>) => Promise<void>;
  onCancel: () => void;
  title?: string;
}

export const NotebookForm: React.FC<NotebookFormProps> = ({
  schema,
  initialData,
  onSubmit,
  onCancel,
  title,
}) => {
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [submitting, setSubmitting] = useState(false);

  // 自动填充/内部字段，不应展示给用户
  const AUTO_FIELDS = ['id', 'created_at', 'updated_at', 'is_ai_gen', 'no', 'seq', 'review_count', 'performance'];

  useEffect(() => {
    if (initialData) {
      setFormData({ ...initialData });
    } else {
      const defaults: Record<string, any> = {};
      schema.columns.forEach((col) => {
        if (AUTO_FIELDS.includes(col.name)) return;
        defaults[col.name] = col.default !== undefined ? col.default : '';
      });
      setFormData(defaults);
    }
  }, [initialData, schema]);

  const handleChange = (name: string, value: any) => {
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

  const renderField = (col: { name: string; type: string; required: boolean }) => {
    if (AUTO_FIELDS.includes(col.name)) {
      return null;
    }

    const value = formData[col.name] ?? '';

    if (col.type === 'boolean' || col.name === 'done') {
      return (
        <div key={col.name} className="flex items-center gap-2">
          <Checkbox
            id={col.name}
            checked={!!value}
            onChange={(e) => handleChange(col.name, e.target.checked)}
          />
          <label htmlFor={col.name} className="text-sm font-medium">
            {col.name}
          </label>
        </div>
      );
    }

    if (col.type === 'text' && col.name === 'content') {
      return (
        <div key={col.name} className="space-y-1">
          <label className="text-sm font-medium">{col.name}</label>
          <Textarea
            value={value}
            onChange={(e) => handleChange(col.name, e.target.value)}
            rows={4}
            required={col.required}
          />
        </div>
      );
    }

    if (col.name === 'note') {
      return (
        <div key={col.name} className="space-y-1">
          <label className="text-sm font-medium">{col.name}</label>
          <Textarea
            value={value}
            onChange={(e) => handleChange(col.name, e.target.value)}
            rows={2}
            required={col.required}
          />
        </div>
      );
    }

    return (
      <div key={col.name} className="space-y-1">
        <label className="text-sm font-medium">{col.name}</label>
        <Input
          value={value}
          onChange={(e) => handleChange(col.name, e.target.value)}
          required={col.required}
          placeholder={col.name}
        />
      </div>
    );
  };

  const editableColumns = schema.columns.filter(
    (c) => !AUTO_FIELDS.includes(c.name),
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
