import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { registerCard } from '@/components/notebook/notebookCards';
import { useNotebookStore } from '@/stores/notebookStore';
import { asEntry } from '@/lib/type-guards';
import type { DiaryEntry } from '@/config/notebook';

const DiaryCard: React.FC<{ entry: Record<string, unknown> }> = ({ entry }) => {
  const schema = useNotebookStore((s) => s.schema);
  const e = asEntry('diary', entry, schema?.columns ?? []);
  return (
    <div className="space-y-1">
      <div className="text-xs text-muted-foreground">{e.date}</div>
      {(e.mood || e.weather) && (
        <div className="text-xs text-muted-foreground">
          {e.mood && `心情: ${e.mood}`}
          {e.mood && e.weather && ' · '}
          {e.weather && `天气: ${e.weather}`}
        </div>
      )}
      <p className="text-sm line-clamp-3">{e.content || '(空)'}</p>
    </div>
  );
};

registerCard('diary', DiaryCard);

export const NotebookDiary: React.FC = () => {
  return <NotebookLayout notetype="diary" />;
};
