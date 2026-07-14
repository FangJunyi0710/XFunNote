import React, { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { NotebookCard } from '@/components/notebook/NotebookCard';
import { useNotebookStore } from '@/stores/notebookStore';

export const NotebookDiary: React.FC = () => {
  const store = useNotebookStore();
  const [dateFilter, setDateFilter] = useState('');

  const quickFilter = (
    <div className="flex items-center gap-2">
      <Input
        type="date"
        value={dateFilter}
        onChange={(e) => setDateFilter(e.target.value)}
        className="w-48"
      />
      <Button
        variant="outline"
        size="sm"
        onClick={() => store.setFilter(dateFilter ? JSON.stringify([[{ column: 'date', op: '=', value: dateFilter }]]) : null)}
      >
        筛选
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => { setDateFilter(''); store.setFilter(null); }}
      >
        全部
      </Button>
    </div>
  );

  return (
    <NotebookLayout
      notetype="diary"
      newLabel="写日记"
      emptyText='暂无日记，点击"写日记"记录今天'
      quickFilter={quickFilter}
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
