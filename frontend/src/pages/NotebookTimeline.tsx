import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { Timestamp } from '@/components/ui/Timestamp';
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


  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {e.start_time && <Timestamp date={e.start_time} from="hour" to="minute" showTimezone={false} />}
        {e.end_time && <span> → </span>}
        {e.end_time && <Timestamp date={e.end_time} from="hour" to="minute" showTimezone={false} />}
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
