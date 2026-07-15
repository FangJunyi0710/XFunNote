import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { registerCard } from '@/components/notebook/notebookCards';
import { useNotebookStore } from '@/stores/notebookStore';
import { asEntry } from '@/lib/type-guards';
import type { WordEntry } from '@/config/notebook';

const WordCard: React.FC<{ entry: Record<string, unknown> }> = ({ entry }) => {
  const schema = useNotebookStore((s) => s.schema);
  const e = asEntry('word', entry, schema?.columns ?? []);
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <span className="font-mono font-bold text-base">{e.word}</span>
        {e.phonetic && (
          <span className="text-sm text-muted-foreground">/{e.phonetic}/</span>
        )}
        {e.part_of_speech && (
          <span className="text-xs text-muted-foreground">({e.part_of_speech})</span>
        )}
      </div>
      {e.example && (
        <p className="text-xs text-muted-foreground line-clamp-1 italic">"{e.example}"</p>
      )}
      <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
        <span>复习 {e.review_count ?? 0} 次</span>
        <span>掌握度 {((e.performance ?? 0) * 100).toFixed(0)}%</span>
        {e.next_review && <span>下次: {e.next_review}</span>}
      </div>
      {e.related_words && (
        <p className="text-xs text-muted-foreground">关联: {e.related_words}</p>
      )}
    </div>
  );
};

registerCard('word', WordCard);

export const NotebookWord: React.FC = () => {
  return (
    <NotebookLayout
      notetype="word"
    />
  );
};
