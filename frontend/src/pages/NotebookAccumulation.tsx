import React, { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { NotebookCard } from '@/components/notebook/NotebookCard';
import { useNotebookStore } from '@/stores/notebookStore';

export const NotebookAccumulation: React.FC = () => {
  const store = useNotebookStore();
  const [sourceFilter, setSourceFilter] = useState('');

  const quickFilter = (
    <div className="flex items-center gap-2">
      <Input
        placeholder="按来源筛选"
        value={sourceFilter}
        onChange={(e) => setSourceFilter(e.target.value)}
        className="w-48"
      />
      <Button
        variant="outline"
        size="sm"
        onClick={() => store.setFilter(sourceFilter ? JSON.stringify([[{ column: 'source', op: 'LIKE', value: sourceFilter }]]) : null)}
      >
        筛选
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => { setSourceFilter(''); store.setFilter(null); }}
      >
        全部
      </Button>
    </div>
  );

  return (
    <NotebookLayout
      notetype="accumulation"
      newLabel="新建"
      emptyText='暂无积累，点击"新建"添加知识'
      quickFilter={quickFilter}
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
