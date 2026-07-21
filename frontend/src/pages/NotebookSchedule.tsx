import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { Timestamp } from '@/components/ui/Timestamp';
import { registerCard } from '@/components/notebook/notebookCards';
import { useCurrentNotebookData } from '@/stores/notebookStore';
import { asEntry } from '@/lib/type-guards';
import type { ScheduleEntry } from '@/config/notebook';

const ScheduleCard: React.FC<{ entry: Record<string, unknown> }> = ({ entry }) => {
  const userData = useCurrentNotebookData();
  const schema = userData?.schema?.columns ?? [];
  const e = asEntry('schedule', entry, schema);
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {e.start_time && <Timestamp date={e.start_time} from="hour" to="minute" showTimezone={false} />}
        {e.end_time && <span> → </span>}
        {e.end_time && <Timestamp date={e.end_time} from="hour" to="minute" showTimezone={false} />}
      </div>
      {e.content && (
        <p className="text-sm font-medium line-clamp-2">{e.content}</p>
      )}
      {e.location && (
        <p className="text-xs text-muted-foreground">{e.location}</p>
      )}
    </div>
  );
};

registerCard('schedule', ScheduleCard);

export const NotebookSchedule: React.FC = () => {
  return <NotebookLayout notetype="schedule" />;
};
