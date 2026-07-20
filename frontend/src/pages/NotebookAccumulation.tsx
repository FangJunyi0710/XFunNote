import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { registerCard } from '@/components/notebook/notebookCards';
import { useCurrentNotebookData } from '@/stores/notebookStore';
import { asEntry } from '@/lib/type-guards';
import type { AccumulationEntry } from '@/config/notebook';

const AccumulationCard: React.FC<{ entry: Record<string, unknown> }> = ({ entry }) => {
  const userData = useCurrentNotebookData();
  const schema = userData?.schema?.columns ?? [];
  const e = asEntry('accumulation', entry, schema);
  return (
    <div className="space-y-1">
      <p className="text-sm text-muted-foreground line-clamp-2">{e.content}</p>
      {e.source && (
        <p className="text-xs text-muted-foreground">来源: {e.source}</p>
      )}
      {e.note && (
        <p className="text-xs text-muted-foreground">备注: {e.note}</p>
      )}
    </div>
  );
};

registerCard('accumulation', AccumulationCard);

export const NotebookAccumulation: React.FC = () => {
  return <NotebookLayout notetype="accumulation" />;
};
