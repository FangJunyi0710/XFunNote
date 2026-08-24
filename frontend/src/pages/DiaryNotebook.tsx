import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { Timestamp } from '@/components/ui/Timestamp';
import { registerCard } from '@/components/notebook/NotebookCard';
import { MarkdownRenderer } from '@/components/ui/MarkdownRenderer';
import { asEntry, type Entry } from '@/types/notebook';

const DiaryCard: React.FC<{ entry: Entry }> = ({ entry }) => {
  const e = asEntry('diary', entry);
  return (
    <div className="space-y-1">
      {(e.date || e.weather || e.mood) && (
        <div className="text-xs text-muted-foreground gap-2 items-center flex">
          {e.date && <Timestamp date={e.date} from="year" to="day" showTimezone={false} />}
          {e.weather && <span>{e.weather}</span>}
          {e.mood && <span>{e.mood}</span>}
        </div>
      )}
      {e.content && <MarkdownRenderer className="text-sm line-clamp-4">{e.content}</MarkdownRenderer>}
    </div>
  );
};

registerCard('diary', DiaryCard);

export const DiaryNotebook: React.FC = () => {
  return <NotebookLayout notetype="diary" />;
};
