import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { registerCard } from '@/components/notebook/notebookCards';
import { useCurrentNotebookData } from '@/stores/notebookStore';
import { MarkdownRenderer } from '@/components/ui/MarkdownRenderer';
import { asEntry } from '@/lib/type-guards';

const AimemoryCard: React.FC<{ entry: Record<string, unknown> }> = ({ entry }) => {
  const userData = useCurrentNotebookData();
  const schema = userData?.schema?.columns ?? [];
  const e = asEntry('aimemory', entry, schema);
  return (
    <div className="space-y-1">
      <span className="font-medium">{e.title || '(无标题)'}</span>
      <MarkdownRenderer className="text-sm text-muted-foreground line-clamp-2">{e.content}</MarkdownRenderer>
      {e.source && (
        <p className="text-xs text-muted-foreground">来源: {e.source}</p>
      )}
    </div>
  );
};

registerCard('aimemory', AimemoryCard);

export const NotebookAimemory: React.FC = () => {
  return <NotebookLayout notetype="aimemory" />;
};
