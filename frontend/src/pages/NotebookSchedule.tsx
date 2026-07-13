import React, { useEffect, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { NotebookCard } from '@/components/notebook/NotebookCard';
import { NotebookForm } from '@/components/notebook/NotebookForm';
import { FilterPanel } from '@/components/notebook/FilterPanel';
import { Pagination } from '@/components/notebook/Pagination';
import { useNotebookStore } from '@/stores/notebookStore';

export const NotebookSchedule: React.FC = () => {
  const store = useNotebookStore();
  const [showForm, setShowForm] = useState(false);
  const [editEntry, setEditEntry] = useState<Record<string, any> | null>(null);

  useEffect(() => {
    store.setCurrentType('schedule');
  }, []);

  const handleSubmit = useCallback(
    async (data: Record<string, any>) => {
      if (editEntry) {
        await store.updateEntry(editEntry.id, data);
      } else {
        await store.addEntries([data]);
      }
      setShowForm(false);
      setEditEntry(null);
    },
    [editEntry, store],
  );

  const handleEdit = useCallback((entry: Record<string, any>) => {
    setEditEntry(entry);
    setShowForm(true);
  }, []);

  const handleDelete = useCallback(
    async (id: string) => {
      if (confirm('确定删除该日程？')) {
        await store.deleteEntries([id]);
      }
    },
    [store],
  );

  const columns = store.schema?.columns.map((c) => ({ name: c.name, type: c.type })) || [];

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">📋 日程</h1>
        <Button onClick={() => { setEditEntry(null); setShowForm(true); }}>
          + 添加日程
        </Button>
      </div>

      <FilterPanel columns={columns} onApply={store.setFilter} />

      {showForm && store.schema && (
        <NotebookForm
          schema={store.schema}
          initialData={editEntry || undefined}
          onSubmit={handleSubmit}
          onCancel={() => { setShowForm(false); setEditEntry(null); }}
          title={editEntry ? '编辑日程' : '添加日程'}
        />
      )}

      {store.loading && <div className="text-sm text-muted-foreground">加载中...</div>}
      {store.error && (
        <div className="text-sm text-destructive bg-destructive/10 p-2 rounded">
          {store.error}
          <button onClick={store.clearError} className="ml-2 underline">关闭</button>
        </div>
      )}

      <div className="space-y-3">
        {!store.loading && store.entries.length === 0 && (
          <div className="text-center py-8 text-muted-foreground text-sm">
            暂无日程
          </div>
        )}
        {store.entries.map((entry) => (
          <NotebookCard
            key={entry.id}
            type="schedule"
            entry={entry}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        ))}
      </div>

      <Pagination
        page={store.page}
        pageSize={store.pageSize}
        total={store.total}
        onPageChange={store.setPage}
        onPageSizeChange={store.setPageSize}
      />
    </div>
  );
};
