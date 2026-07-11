import React, { useEffect, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { NotebookCard } from '@/components/notebook/NotebookCard';
import { NotebookForm } from '@/components/notebook/NotebookForm';
import { Pagination } from '@/components/notebook/Pagination';
import { useNotebookStore } from '@/stores/notebookStore';

export const NotebookDiary: React.FC = () => {
  const store = useNotebookStore();
  const [showForm, setShowForm] = useState(false);
  const [editEntry, setEditEntry] = useState<Record<string, any> | null>(null);
  const [dateFilter, setDateFilter] = useState('');

  useEffect(() => {
    store.setCurrentType('diary');
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
      if (confirm('确定删除这篇日记？')) {
        await store.deleteEntries([id]);
      }
    },
    [store],
  );

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">📝 日记</h1>
        <Button onClick={() => { setEditEntry(null); setShowForm(true); }}>
          + 写日记
        </Button>
      </div>

      {/* 日期筛选 */}
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
          onClick={() => store.setFilter(dateFilter ? JSON.stringify({ cond: { column: 'date', op: 'eq', value: dateFilter } }) : null)}
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

      {/* 表单 */}
      {showForm && store.schema && (
        <NotebookForm
          schema={store.schema}
          initialData={editEntry || undefined}
          onSubmit={handleSubmit}
          onCancel={() => { setShowForm(false); setEditEntry(null); }}
          title={editEntry ? '编辑日记' : '写日记'}
        />
      )}

      {store.loading && <div className="text-sm text-muted-foreground">加载中...</div>}
      {store.error && (
        <div className="text-sm text-destructive bg-destructive/10 p-2 rounded">
          {store.error}
          <button onClick={store.clearError} className="ml-2 underline">关闭</button>
        </div>
      )}

      {/* 时间线 */}
      <div className="space-y-3">
        {!store.loading && store.entries.length === 0 && (
          <div className="text-center py-8 text-muted-foreground text-sm">
            暂无日记，点击"写日记"记录今天
          </div>
        )}
        {store.entries.map((entry) => (
          <NotebookCard
            key={entry.id}
            type="diary"
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
