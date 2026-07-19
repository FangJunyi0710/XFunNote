import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { registerCard } from '@/components/notebook/notebookCards';
import { useNotebookStore } from '@/stores/notebookStore';
import { asEntry } from '@/lib/type-guards';

const LedgerCard: React.FC<{ entry: Record<string, unknown> }> = ({ entry }) => {
  const schema = useNotebookStore((s) => s.schema);
  const e = asEntry('ledger', entry, schema?.columns ?? []);
  return (
    <div className="space-y-1">
      <div className="text-xs text-muted-foreground">{e.date}</div>
      {e.account && <div className="text-xs text-muted-foreground">账户：{e.account}</div>}
      <div className="font-mono text-sm">
        {e.amount !== undefined && e.amount !== null ? (
          <span className={e.amount >= 0 ? 'text-green-600' : 'text-red-600'}>
            {e.amount > 0 ? '+' : ''}{e.amount}
          </span>
        ) : null}
      </div>
      <p className="text-sm line-clamp-3">{e.content || '(空)'}</p>
    </div>
  );
};

registerCard('ledger', LedgerCard);

export const NotebookLedger: React.FC = () => {
  return <NotebookLayout notetype="ledger" />;
};
