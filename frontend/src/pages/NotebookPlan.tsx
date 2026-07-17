import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { registerCard } from '@/components/notebook/notebookCards';
import { Badge } from '@/components/ui/badge';
import { useNotebookStore } from '@/stores/notebookStore';
import { asEntry } from '@/lib/type-guards';
import type { PlanEntry } from '@/config/notebook';

const PlanCard: React.FC<{ entry: Record<string, unknown> }> = ({ entry }) => {
  const schema = useNotebookStore((s) => s.schema);
  const e = asEntry('plan', entry, schema?.columns ?? []);
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {e.no && <span className="font-mono">{e.no}</span>}
        <span>{e.month}</span>
        {e.done ? (
          <Badge variant="success" className="text-[10px]">已完成</Badge>
        ) : (
          <Badge variant="secondary" className="text-[10px]">未完成</Badge>
        )}
      </div>
      {e.content && (
        <p className="text-sm font-medium line-clamp-3">{e.content}</p>
      )}
    </div>
  );
};

registerCard('plan', PlanCard);

export const NotebookPlan: React.FC = () => {
  return <NotebookLayout notetype="plan" />;
};
