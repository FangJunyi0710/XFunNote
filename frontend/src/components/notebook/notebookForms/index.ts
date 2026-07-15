import React from 'react';

export type FormRenderer = React.FC<{
  schema: any;
  initialData?: Record<string, any>;
  onSubmit: (data: Record<string, any>) => Promise<void>;
  onCancel: () => void;
  title?: string;
  disableRequired?: boolean;
}>;

const registry = new Map<string, FormRenderer>();

export function registerForm(type: string, renderer: FormRenderer): void {
  registry.set(type, renderer);
}

export function getFormRenderer(type: string): FormRenderer | undefined {
  return registry.get(type);
}
