import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { Timestamp } from '@/components/ui/Timestamp';
import { registerCard } from '@/components/notebook/NotebookCard';
import { asEntry, type Entry } from '@/types/notebook';

const WordCard: React.FC<{ entry: Entry }> = ({ entry }) => {
  const e = asEntry('word', entry);
  return (
    <div className="space-y-1">
      {(e.word || e.phonetic || e.part_of_speech) && (
        <div className="flex items-center gap-2">
          {e.word && <span className="font-mono font-bold text-base">{e.word}</span>}
          {e.phonetic && (
            <span className="text-sm text-muted-foreground">/{e.phonetic}/</span>
          )}
          {e.part_of_speech && (
            <span className="text-xs text-muted-foreground">{e.part_of_speech}</span>
          )}
        </div>
      )}
      {e.example && (
        <p className="text-xs text-muted-foreground line-clamp-2">{e.example}</p>
      )}
      {(e.review_count !== null || e.stability !== null || e.difficulty !== null || e.next_review) && (
        <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
          {e.review_count !== null && (
            <span>复习 {e.review_count} 次</span>
          )}
          {e.stability !== null && (
            <span>稳定性 {e.stability.toFixed(1)}d</span>
          )}
          {e.difficulty !== null && (
            <span>难度 {e.difficulty.toFixed(1)}</span>
          )}
          {e.next_review && <span>下次: <Timestamp date={e.next_review} from="year" to="day" showTimezone={false} /></span>}
        </div>
      )}
      {e.related_words && (
        <p className="text-xs text-muted-foreground">关联: {e.related_words}</p>
      )}
    </div>
  );
};

registerCard('word', WordCard);

export const WordNotebook: React.FC = () => {
  return <NotebookLayout notetype="word" />;
};
