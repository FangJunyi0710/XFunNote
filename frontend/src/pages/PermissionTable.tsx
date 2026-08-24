import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { registerCard } from '@/components/notebook/NotebookCard';
import { asEntry, type Entry } from '@/types/notebook';

const PermissionCard: React.FC<{ entry: Entry }> = ({ entry }) => {
  const e = asEntry('_permission', entry);
  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold">{e.name || '（未命名）'}</span>
      </div>
      {e.description && (
        <p className="text-xs text-muted-foreground line-clamp-2">{e.description}</p>
      )}
      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span>
          <span className={e.read_view ? 'text-green-600 dark:text-green-400' : ''}>●</span> 读视图
        </span>
        <span>
          <span className={e.write_view ? 'text-green-600 dark:text-green-400' : ''}>●</span> 写视图
        </span>
      </div>
    </div>
  );
};

registerCard('_permission', PermissionCard);

export const PermissionTable: React.FC = () => {
  return <NotebookLayout notetype="_permission" />;
};
