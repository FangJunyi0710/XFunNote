import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { registerCard } from '@/components/notebook/NotebookCard';
import { MarkdownRenderer } from '@/components/ui/MarkdownRenderer';
import { asEntry, type Entry } from '@/types/notebook';

const AccumulationCard: React.FC<{ entry: Entry }> = ({ entry }) => {
  const e = asEntry('accumulation', entry);
  return (
    <div className="space-y-1">
      <MarkdownRenderer className="text-sm line-clamp-4">{e.content}</MarkdownRenderer>
      {e.source && (
        <p className="text-xs text-muted-foreground">来源: {e.source}</p>
      )}
    </div>
  );
};

registerCard('accumulation', AccumulationCard);

export const NotebookAccumulation: React.FC = () => {
  return <NotebookLayout notetype="accumulation" />;
};
