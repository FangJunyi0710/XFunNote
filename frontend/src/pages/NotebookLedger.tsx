import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { Timestamp } from '@/components/ui/Timestamp';
import { registerCard } from '@/components/notebook/notebookCards';
import { useCurrentNotebookData } from '@/stores/notebookStore';
import { asEntry } from '@/lib/type-guards';

const LedgerCard: React.FC<{ entry: Record<string, unknown> }> = ({ entry }) => {
  const userData = useCurrentNotebookData();
  const schema = userData?.schema?.columns ?? [];
  const e = asEntry('ledger', entry, schema);
  return (
    <div className="space-y-1">
      <div className="text-xs text-muted-foreground"><Timestamp date={e.date} from="year" to="day" showTimezone={false} /></div>
      {e.account && <div className="text-xs text-muted-foreground">账户：{e.account}</div>}
      <div className="font-mono text-sm">
        {e.amount_cents !== undefined && e.amount_cents !== null ? (
          <span className={e.amount_cents >= 0 ? 'text-green-600' : 'text-red-600'}>
            {e.amount_cents > 0 ? '+' : ''}{(e.amount_cents / 100).toFixed(2)}
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
