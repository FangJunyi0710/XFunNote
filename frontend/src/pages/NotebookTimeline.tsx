import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { registerCard } from '@/components/notebook/notebookCards';
import { useCurrentNotebookData } from '@/stores/notebookStore';
import { asEntry } from '@/lib/type-guards';
import type { TimelineEntry } from '@/config/notebook';

const TimelineCard: React.FC<{ entry: Record<string, unknown> }> = ({ entry }) => {
  const userData = useCurrentNotebookData();
  const schema = userData?.schema?.columns ?? [];
  const e = asEntry('timeline', entry, schema);

  // 计算持续时间（分钟）
  const formatDuration = (start: string, end: string) => {
    if (!start || !end) return null;
    const diffMs = new Date(end).getTime() - new Date(start).getTime();
    if (diffMs <= 0) return null;
    const minutes = Math.floor(diffMs / 60000);
    if (minutes < 1) return '<1min';
    if (minutes < 60) return `${minutes}min`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}min` : `${hours}h`;
  };

  const duration = e.start_time && e.end_time ? formatDuration(e.start_time, e.end_time) : null;

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {e.start_time && <span>{e.start_time}</span>}
        {e.end_time && <span>→ {e.end_time}</span>}
        {duration && <span>({duration})</span>}
      </div>
      {e.content && (
        <p className="text-sm line-clamp-2">{e.content}</p>
      )}
      {e.location && (
        <p className="text-xs text-muted-foreground">{e.location}</p>
      )}
    </div>
  );
};

registerCard('timeline', TimelineCard);

export const NotebookTimeline: React.FC = () => {
  return <NotebookLayout notetype="timeline" />;
};
