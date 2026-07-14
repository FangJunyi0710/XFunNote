import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { NotebookCard } from '@/components/notebook/NotebookCard';

export const NotebookDiary: React.FC = () => {

  return (
    <NotebookLayout
      notetype="diary"
      renderCardList={({ entries, onEdit, onDelete }) => (
        <div className="space-y-3">
          {entries.map((entry) => (
            <NotebookCard
              key={entry.id}
              type="diary"
              entry={entry}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    />
  );
};
