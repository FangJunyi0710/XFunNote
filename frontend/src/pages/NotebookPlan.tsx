import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { registerCard } from '@/components/notebook/NotebookCard';
import { MarkdownRenderer } from '@/components/ui/MarkdownRenderer';
import { asEntry, type Entry } from '@/types/notebook';

const PlanCard: React.FC<{ entry: Entry }> = ({ entry }) => {
  const e = asEntry('plan', entry);
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {e.no && <span className="font-mono">{e.no}</span>}
        {e.done ? (
          <span className="text-[10px] text-green-600 font-medium">已完成</span>
        ) : (
          <span className="text-[10px] text-gray-500">未完成</span>
        )}
      </div>
      {e.content && (
        <MarkdownRenderer className="text-sm font-medium line-clamp-3">{e.content}</MarkdownRenderer>
      )}
    </div>
  );
};

registerCard('plan', PlanCard);

export const NotebookPlan: React.FC = () => {
  return <NotebookLayout notetype="plan" />;
};
