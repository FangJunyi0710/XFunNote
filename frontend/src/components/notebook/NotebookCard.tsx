import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { formatDateTime } from '@/lib/utils';
import { getCardRenderer } from '@/components/notebook/notebookCards';
import { getNotebookStyles } from '@/config/notebook';
import type { NotebookType } from '@/config/notebook';

interface NotebookCardProps {
  type: string;
  entry: Record<string, any>;
  selected?: boolean;
  onSelect?: (id: string) => void;
  onEdit?: (entry: Record<string, any>) => void;
  onDelete?: (id: string) => void;
}

export const NotebookCard: React.FC<NotebookCardProps> = ({
  type,
  entry,
  selected,
  onSelect,
  onEdit,
  onDelete,
}) => {
  const navigate = useNavigate();
  const Renderer = getCardRenderer(type);
  const styles = getNotebookStyles(type as NotebookType);

  return (
    <Card
      className={`border-l-4 ${styles.border} cursor-pointer transition-shadow hover:shadow-md ${
        selected ? `ring-2 ${styles.ring}` : ''
      }`}
      onClick={() => onSelect?.(entry.id)}
    >
      <CardContent className="p-4">
        {Renderer ? (
          <Renderer entry={entry} />
        ) : (
          <pre className="text-xs">{JSON.stringify(entry, null, 2)}</pre>
        )}
        <div className="flex justify-between items-center mt-2 pt-2 border-t border-border/50">
          <span className="text-[10px] text-muted-foreground">
            {formatDateTime(entry.created_at)}
          </span>
          <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
            <button
              className="text-xs text-primary hover:underline"
              onClick={() => navigate(`/notebooks/${type}/edit/${entry.id}`)}
            >
              编辑
            </button>
            <button
              className="text-xs text-destructive hover:underline"
              onClick={() => onDelete?.(entry.id)}
            >
              删除
            </button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
