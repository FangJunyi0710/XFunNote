import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { registerCard } from '@/components/notebook/notebookCards';
import { useNotebookStore } from '@/stores/notebookStore';
import { asEntry } from '@/lib/type-guards';
import type { TimelineEntry } from '@/config/notebook';

const TimelineCard: React.FC<{ entry: Record<string, unknown> }> = ({ entry }) => {
  const schema = useNotebookStore((s) => s.schema);
  const e = asEntry('timeline', entry, schema?.columns ?? []);
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {e.start_time && <span>{e.start_time}</span>}
        {e.end_time && <span>→ {e.end_time}</span>}
        {e.duration && <span>({e.duration})</span>}
      </div>
      {e.content && (
        <p className="text-sm line-clamp-2">{e.content}</p>
      )}
      {e.location && (
        <p className="text-xs text-muted-foreground">📍 {e.location}</p>
      )}
    </div>
  );
};

registerCard('timeline', TimelineCard);

export const NotebookTimeline: React.FC = () => {
  return (
    <NotebookLayout
      notetype="timeline"
    />
  );
};
