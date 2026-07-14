import React, { useEffect, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { NotebookCard } from '@/components/notebook/NotebookCard';
import { NotebookForm } from '@/components/notebook/NotebookForm';
import { FilterPanel } from '@/components/notebook/FilterPanel';
import { Pagination } from '@/components/notebook/Pagination';
import { useNotebookStore } from '@/stores/notebookStore';

export const NotebookPlan: React.FC = () => {
  const store = useNotebookStore();
  const [showForm, setShowForm] = useState(false);
  const [editEntry, setEditEntry] = useState<Record<string, any> | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [monthFilter, setMonthFilter] = useState('');

  useEffect(() => {
    store.setCurrentType('plan');
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
      if (confirm('确定删除该计划？')) {
        await store.deleteEntries([id]);
      }
    },
    [store],
  );

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

  const columns = store.schema?.columns.map((c) => ({ name: c.name, type: c.type })) || [];

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">📋 计划</h1>
        <div className="flex items-center gap-2">
          {monthFilter && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setMonthFilter('')}
            >
              清除月份
            </Button>
          )}
          {selectedIds.size > 0 && (
            <Button variant="destructive" size="sm" onClick={handleBatchDelete}>
              删除 {selectedIds.size} 项
            </Button>
          )}
          <Button onClick={() => { setEditEntry(null); setShowForm(true); }}>
            + 新建
          </Button>
        </div>
      </div>

      {/* 月份快捷筛选 */}
      <div className="flex items-center gap-2">
        <Input
          placeholder="按月份筛选 (如 2025-03)"
          value={monthFilter}
          onChange={(e) => setMonthFilter(e.target.value)}
          className="w-48"
        />
        <Button
          variant="outline"
          size="sm"
          onClick={() => store.setFilter(monthFilter ? JSON.stringify([[{ column: 'month', op: 'LIKE', value: monthFilter }]]) : null)}
        >
          筛选
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => store.setFilter(null)}
        >
          全部
        </Button>
      </div>

      <FilterPanel columns={columns} onApply={store.setFilter} />

      {/* 表单抽屉 */}
      {showForm && store.schema && (
        <NotebookForm
          schema={store.schema}
          initialData={editEntry || undefined}
          onSubmit={handleSubmit}
          onCancel={() => { setShowForm(false); setEditEntry(null); }}
          title={editEntry ? '编辑计划' : '新建计划'}
        />
      )}

      {/* 加载/错误 */}
      {store.loading && <div className="text-sm text-muted-foreground">加载中...</div>}
      {store.error && (
        <div className="text-sm text-destructive bg-destructive/10 p-2 rounded">
          {store.error}
          <button onClick={store.clearError} className="ml-2 underline">关闭</button>
        </div>
      )}

      {/* 列表 */}
      <div className="space-y-3">
        {!store.loading && store.entries.length === 0 && (
          <div className="text-center py-8 text-muted-foreground text-sm">
            暂无计划，点击"新建"添加第一条
          </div>
        )}
        {store.entries.map((entry) => (
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
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            </div>
          </div>
        ))}
      </div>

      {/* 分页 */}
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
