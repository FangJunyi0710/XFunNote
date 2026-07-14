import React, { useEffect, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { NotebookCard } from '@/components/notebook/NotebookCard';
import { NotebookForm } from '@/components/notebook/NotebookForm';
import { FilterPanel } from '@/components/notebook/FilterPanel';
import { Pagination } from '@/components/notebook/Pagination';
import { useNotebookStore } from '@/stores/notebookStore';

export const NotebookAccumulation: React.FC = () => {
  const store = useNotebookStore();
  const [showForm, setShowForm] = useState(false);
  const [editEntry, setEditEntry] = useState<Record<string, any> | null>(null);
  const [sourceFilter, setSourceFilter] = useState('');

  useEffect(() => {
    store.setCurrentType('accumulation');
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
      if (confirm('确定删除该条目？')) {
        await store.deleteEntries([id]);
      }
    },
    [store],
  );

  const columns = store.schema?.columns.map((c) => ({ name: c.name, type: c.type })) || [];

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">📚 积累</h1>
        <Button onClick={() => { setEditEntry(null); setShowForm(true); }}>
          + 新建
        </Button>
      </div>

      {/* 来源快捷筛选 */}
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

      <FilterPanel columns={columns} onApply={store.setFilter} />

      {showForm && store.schema && (
        <NotebookForm
          schema={store.schema}
          initialData={editEntry || undefined}
          onSubmit={handleSubmit}
          onCancel={() => { setShowForm(false); setEditEntry(null); }}
          title={editEntry ? '编辑积累' : '新建积累'}
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
            暂无积累，点击"新建"添加知识
          </div>
        )}
        {store.entries.map((entry) => (
          <NotebookCard
            key={entry.id}
            type="accumulation"
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
