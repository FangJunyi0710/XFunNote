import React, { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';
import { NotebookCard } from '@/components/notebook/NotebookCard';
import { useNotebookStore } from '@/stores/notebookStore';

export const NotebookPlan: React.FC = () => {
  const store = useNotebookStore();
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const handleBatchDelete = useCallback(async () => {
    if (selectedIds.size === 0) return;
    if (confirm(`确定删除 ${selectedIds.size} 条计划？`)) {
      await store.deleteEntries(Array.from(selectedIds));
      setSelectedIds(new Set());
    }
  }, [selectedIds, store]);

  const toggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const batchActions = selectedIds.size > 0 ? (
    <Button variant="destructive" size="sm" onClick={handleBatchDelete}>
      删除 {selectedIds.size} 项
    </Button>
  ) : null;

  return (
    <NotebookLayout
      notetype="plan"
      batchActions={batchActions}
      renderCardList={({ entries, onEdit, onDelete }) => (
        <div className="space-y-3">
          {entries.map((entry) => (
            <div key={entry.id} className="flex items-start gap-2">
              <input
                type="checkbox"
                className="mt-4"
                checked={selectedIds.has(entry.id)}
                onChange={() => toggleSelect(entry.id)}
              />
              <div className="flex-1">
                <NotebookCard
                  type="plan"
                  entry={entry}
                  onEdit={onEdit}
                  onDelete={onDelete}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    />
  );
};
