import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { registerCard } from '@/components/notebook/NotebookCard';
import { asEntry, type Entry } from '@/types/notebook';
import { maskKey } from '@/lib/utils';
import { cn } from '@/lib/utils';

const TokenCard: React.FC<{ entry: Entry }> = ({ entry }) => {
  const e = asEntry('_token', entry);
  const isActive = e.is_active === 1;
  return (
    <div className="space-y-1.5">
      {(e.name || e.is_active !== null) && (
        <div className="flex items-center justify-between">
          {e.name && <span className="text-sm font-semibold">{e.name}</span>}
          {e.is_active !== null && (
            <span className={cn('text-[10px] font-medium px-1.5 py-0.5 rounded',
              isActive ? 'text-green-600 bg-green-600/10' : 'text-red-600 bg-red-600/10')}>
              {isActive ? '启用' : '停用'}
            </span>
          )}
        </div>
      )}
      {e.token && (
        <div className="text-xs font-mono text-muted-foreground">{maskKey(e.token)}</div>
      )}
      {e.shortcut && (
        <div className="text-xs">
          <span className="text-muted-foreground">快捷码: </span>
          <span className="font-mono text-amber-600 dark:text-amber-400">{e.shortcut}</span>
        </div>
      )}
      {e.permission && (
        <div className="text-xs text-muted-foreground truncate">
          权限: {e.permission}
        </div>
      )}
    </div>
  );
};

registerCard('_token', TokenCard);

export const TokenTable: React.FC = () => {
  return <NotebookLayout notetype="_token" />;
};
