import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { registerCard } from '@/components/notebook/NotebookCard';
import { MarkdownRenderer } from '@/components/ui/MarkdownRenderer';
import { asEntry, type Entry } from '@/types/notebook';

const AimemoryCard: React.FC<{ entry: Entry }> = ({ entry }) => {
  const e = asEntry('aimemory', entry);
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <span className="font-medium">{e.title || '(无标题)'}</span>
        {e.source && (
          <span className="text-xs text-muted-foreground">来源: {e.source}</span>
        )}
      </div>
      <MarkdownRenderer className="text-sm text-muted-foreground line-clamp-2">{e.content}</MarkdownRenderer>

    </div>
  );
};

registerCard('aimemory', AimemoryCard);

export const AimemoryNotebook: React.FC = () => {
  return <NotebookLayout notetype="aimemory" />;
};
