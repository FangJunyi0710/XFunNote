import React, { useMemo } from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { Timestamp } from '@/components/ui/Timestamp';
import { registerCard } from '@/components/notebook/NotebookCard';
import { MarkdownRenderer } from '@/components/ui/MarkdownRenderer';
import { getColorFromString } from '@/lib/utils';
import { asEntry, type Entry } from '@/types/notebook';

const LedgerCard: React.FC<{ entry: Entry }> = ({ entry }) => {
  const transactionId = entry['transaction_id'] as string | undefined;
  const color = useMemo(
    () => (transactionId ? getColorFromString(transactionId) : undefined),
    [transactionId]
  );
  const e = asEntry('ledger', entry);
  return (
    <div className="space-y-1">
      {transactionId && (
        <span className="flex items-center gap-1.5 text-[10px] font-mono text-muted-foreground" style={{ color: color }}>
          {transactionId}
        </span>
      )}
      {(e.date || e.account || e.amount_cents !== null) && (
        <div className="text-xs text-muted-foreground gap-2 items-center flex">
          {e.date && <Timestamp date={e.date} from="year" to="day" showTimezone={false} />}
          {e.account && <span className="text-xs text-muted-foreground">{e.account}</span>}
          {e.amount_cents !== null && (
            <span className="font-mono text-sm">
              <span className={e.amount_cents >= 0 ? 'text-green-600' : 'text-red-600'}>
                {e.amount_cents > 0 ? '+' : ''}{(e.amount_cents / 100).toFixed(2)}
              </span>
            </span>
          )}
        </div>
      )}
      {e.content && <MarkdownRenderer className="text-sm line-clamp-3">{e.content}</MarkdownRenderer>}
    </div>
  );
};

registerCard('ledger', LedgerCard);

export const LedgerNotebook: React.FC = () => {
  return <NotebookLayout notetype="ledger" />;
};
