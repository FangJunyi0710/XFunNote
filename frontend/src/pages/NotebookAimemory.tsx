import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { registerCard } from '@/components/notebook/notebookCards';
import { useNotebookStore } from '@/stores/notebookStore';
import { asEntry } from '@/lib/type-guards';
import type { AimemoryEntry } from '@/config/notebook';

const AimemoryCard: React.FC<{ entry: Record<string, unknown> }> = ({ entry }) => {
  const schema = useNotebookStore((s) => s.schema);
  const e = asEntry('aimemory', entry, schema?.columns ?? []);
  return (
    <div className="space-y-1">
      <span className="font-medium">{e.title || '(无标题)'}</span>
      <p className="text-sm text-muted-foreground line-clamp-2">{e.content}</p>
      {e.source && (
        <p className="text-xs text-muted-foreground">来源: {e.source}</p>
      )}
    </div>
  );
};

registerCard('aimemory', AimemoryCard);

export const NotebookAimemory: React.FC = () => {
  return (
    <NotebookLayout
      notetype="aimemory"
    />
  );
};
