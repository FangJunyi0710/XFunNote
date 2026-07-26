import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Timestamp } from '@/components/ui/Timestamp';
import { getCardRenderer } from '@/components/notebook/notebookCards';
import { getNotebookStyles } from '@/config/notebook';
import type { NotebookType } from '@/config/notebook';
import { EditIcon } from '@/components/ui/icons';

interface NotebookCardProps {
  type: string;
  entry: Record<string, unknown>;
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
      className={`border-2 border-border cursor-pointer transition-all hover:shadow-md ${
        selected ? `ring-2 ${styles.ring} !bg-accent` : ''
      }`}
      onClick={() => onSelect?.(entry['id'] as string)}
    >
      <CardContent className="p-4">
        {Renderer ? (
          <Renderer entry={entry} />
        ) : (
          <pre className="text-xs">{JSON.stringify(entry, null, 2)}</pre>
        )}
        <div className="flex justify-between items-center mt-2 pt-2 border-t border-border/30">
          <div className="flex flex-col text-xs text-muted-foreground space-y-0.5">
            <Timestamp date={created} />
            {showUpdated && <Timestamp date={updated} />}
          </div>
          <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
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