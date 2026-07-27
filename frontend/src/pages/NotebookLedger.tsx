import React, { useMemo } from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { Timestamp } from '@/components/ui/Timestamp';
import { registerCard } from '@/components/notebook/NotebookCard';
import { MarkdownRenderer } from '@/components/ui/MarkdownRenderer';
import { useCurrentNotebookData } from '@/stores/notebookStore';
import { asEntry } from '@/lib/type-guards';
import { getColorFromString } from '@/lib/utils';

const LedgerCard: React.FC<{ entry: Record<string, unknown> }> = ({ entry }) => {
  const transactionId = entry['transaction_id'] as string | undefined;
  const color = useMemo(
    () => (transactionId ? getColorFromString(transactionId) : undefined),
    [transactionId]
  );

  const userData = useCurrentNotebookData();
  const schema = userData?.schema?.columns ?? [];
  const e = asEntry('ledger', entry, schema);
  return (
    <div className="space-y-1">
      {transactionId && (
        <span className="flex items-center gap-1.5 text-[10px] font-mono text-muted-foreground" style={{ color: color }}>
          {transactionId}
        </span>
      )}
      <div className="text-xs text-muted-foreground">
        <Timestamp date={e.date} from="year" to="day" showTimezone={false} />
        {e.account && <span className="text-xs text-muted-foreground ml-2">{e.account}</span>}
        <span className="font-mono text-sm ml-2">
          {e.amount_cents !== undefined && e.amount_cents !== null ? (
            <span className={e.amount_cents >= 0 ? 'text-green-600' : 'text-red-600'}>
              {e.amount_cents > 0 ? '+' : ''}{(e.amount_cents / 100).toFixed(2)}
            </span>
          ) : null}
        </span>
      </div>
      <MarkdownRenderer className="text-sm line-clamp-3">{e.content || '(空)'}</MarkdownRenderer>
    </div>
  );
};

registerCard('ledger', LedgerCard);

export const NotebookLedger: React.FC = () => {
  return <NotebookLayout notetype="ledger" />;
};
