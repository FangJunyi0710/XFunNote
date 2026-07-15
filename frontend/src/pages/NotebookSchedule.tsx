import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { registerCard } from '@/components/notebook/notebookCards';
import { Badge } from '@/components/ui/badge';
import type { ScheduleEntry } from '@/config/notebook';

const ScheduleCard: React.FC<{ entry: Record<string, any> }> = ({ entry }) => {
  const e = entry as unknown as ScheduleEntry;
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {e.start_time && <span>{e.start_time}</span>}
        {e.end_time && <span>→ {e.end_time}</span>}
        {e.done ? (
          <Badge variant="success" className="text-[10px]">已完成</Badge>
        ) : (
          <Badge variant="secondary" className="text-[10px]">待办</Badge>
        )}
      </div>
      {e.content && (
        <p className="text-sm font-medium line-clamp-2">{e.content}</p>
      )}
      {e.location && (
        <p className="text-xs text-muted-foreground">📍 {e.location}</p>
      )}
    </div>
  );
};

registerCard('schedule', ScheduleCard);

export const NotebookSchedule: React.FC = () => {
  return (
    <NotebookLayout
      notetype="schedule"
    />
  );
};
