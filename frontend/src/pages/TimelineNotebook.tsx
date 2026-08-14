import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { Timestamp } from '@/components/ui/Timestamp';
import { registerCard } from '@/components/notebook/NotebookCard';
import { MarkdownRenderer } from '@/components/ui/MarkdownRenderer';
import { asEntry, type Entry } from '@/types/notebook';

const TimelineCard: React.FC<{ entry: Entry }> = ({ entry }) => {
  const e = asEntry('timeline', entry);
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {e.start_time && <Timestamp date={e.start_time} from="month" to="minute" showTimezone={false} />}
        {e.end_time && <><span> - </span><Timestamp date={e.end_time} from="hour" to="minute" showTimezone={false} /></>}
        <p className="text-xs text-muted-foreground">{e.location}</p>
      </div>
      {e.content && (
        <MarkdownRenderer className="text-sm font-medium line-clamp-2">{e.content}</MarkdownRenderer>
      )}
    </div>
  );
};

registerCard('timeline', TimelineCard);

export const TimelineNotebook: React.FC = () => {
  return <NotebookLayout notetype="timeline" />;
};
