import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Timestamp } from '@/components/ui/Timestamp';
import { getNotebookStyles } from '@/config/notebook';
import type { NotebookType } from '@/config/notebook';
import { EditIcon } from '@/components/ui/icons';
import { cn } from '@/lib/utils';
import type { Entry } from '@/types/notebook';

export type CardRenderer = React.FC<{ entry: Entry }>;

const registry = new Map<string, CardRenderer>();

export const registerCard = (type: NotebookType, renderer: CardRenderer): void => {
  registry.set(type, renderer);
}

export const getCardRenderer = (type: string): CardRenderer | undefined => registry.get(type);

interface NotebookCardProps {
  type: string;
  entry: Entry;
  selected?: boolean;
  onSelect?: (id: string) => void;
}

export const NotebookCard: React.FC<NotebookCardProps> = React.memo(({
  type,
  entry,
  selected,
  onSelect,
}) => {
  const navigate = useNavigate();
  const Renderer = getCardRenderer(type);
  const styles = getNotebookStyles(type as NotebookType);

  const created = entry['created_at'] as string | undefined;
  const updated = entry['updated_at'] as string | undefined;
  const showUpdated = updated && updated !== created;

  return (
    <Card
      className={cn('border-2 border-border cursor-pointer transition-all hover:shadow-md',
        selected && `ring-2 ${styles.ring} !bg-accent`)}
      onClick={() => onSelect?.(entry['id'] as string)}
    >
      <CardContent>
        {Renderer ? (
          <Renderer entry={entry} />
        ) : (
          <pre className="text-xs">{JSON.stringify(entry, null, 2)}</pre>
        )}
        <div className="flex justify-between items-center border-t border-border/30 -mb-5">
          <div className="flex flex-col text-xs text-muted-foreground space-y-0.5">
            {created && <Timestamp date={created} />}
            {showUpdated && <Timestamp date={updated} />}
          </div>
          <div className="flex gap-1" onClick={e => e.stopPropagation()}>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/notebooks/${type}/edit/${entry['id'] as string}`)}
            >
              <EditIcon />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
});
