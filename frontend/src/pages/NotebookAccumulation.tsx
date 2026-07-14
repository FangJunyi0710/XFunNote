import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { NotebookCard } from '@/components/notebook/NotebookCard';

export const NotebookAccumulation: React.FC = () => {

  return (
    <NotebookLayout
      notetype="accumulation"
      renderCardList={({ entries, onEdit, onDelete }) => (
        <div className="space-y-3">
          {entries.map((entry) => (
            <NotebookCard
              key={entry.id}
              type="accumulation"
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
