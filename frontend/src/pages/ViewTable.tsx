import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { registerCard } from '@/components/notebook/NotebookCard';
import { asEntry, type Entry } from '@/types/notebook';

const ViewCard: React.FC<{ entry: Entry }> = ({ entry }) => {
  const e = asEntry('_view', entry);
  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold">{e.name || '（未命名）'}</span>
      </div>
      {e.data && (
        <pre className="text-xs font-mono text-muted-foreground line-clamp-3 whitespace-pre-wrap break-all">
          {e.data}
        </pre>
      )}
    </div>
  );
};

registerCard('_view', ViewCard);

export const ViewTable: React.FC = () => {
  return <NotebookLayout notetype="_view" />;
};
