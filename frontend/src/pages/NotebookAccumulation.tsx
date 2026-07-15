import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { registerCard } from '@/components/notebook/notebookCards';
import type { AccumulationEntry } from '@/types/notebook';

const AccumulationCard: React.FC<{ entry: Record<string, any> }> = ({ entry }) => {
  const e = entry as unknown as AccumulationEntry;
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
