import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { NotebookCard } from '@/components/notebook/NotebookCard';
import { Pagination } from '@/components/notebook/Pagination';
import { useNotebookStore } from '@/stores/notebookStore';

export const NotebookDiary: React.FC = () => {
  const store = useNotebookStore();

  return (
    <NotebookLayout
      notetype="diary"
      renderEntryDisplay={({ entries, onEdit, onDelete }) => ({
        stickySlot: entries.length > 0 ? (
          <Pagination
            page={store.page}
            pageSize={store.pageSize}
            total={store.total}
            onPageChange={store.setPage}
            onPageSizeChange={store.setPageSize}
          />
        ) : undefined,
        content: (
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
        ),
      })}
    />
  );
};
