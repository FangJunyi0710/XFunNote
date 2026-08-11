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
      <div className="text-xs text-muted-foreground gap-2 items-center flex">
        <Timestamp date={e.date} from="year" to="day" showTimezone={false} />
        <span>{e.weather}</span>
        <span>{e.mood}</span>
      </div>
      <MarkdownRenderer className="text-sm line-clamp-4">{e.content || '(空)'}</MarkdownRenderer>
    </div>
  );
};

registerCard('diary', DiaryCard);

export const NotebookDiary: React.FC = () => {
  return <NotebookLayout notetype="diary" />;
};
