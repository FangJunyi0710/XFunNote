import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { defaultRenderEntryDisplay } from '@/components/notebook/notebookCards/defaultCardList';
import { useNotebookStore } from '@/stores/notebookStore';
import * as notebookApi from '@/api/notebooks';
import { TYPE_LABELS, DEFAULT_EMOJIS } from '@/config/notebook';
import type { NotebookType } from '@/config/notebook';

interface NotebookLayoutProps {
  /** 笔记本类型标识 */
  notetype: NotebookType;
  /** 标题 emoji */
  emoji?: string;
  /** 自定义条目展示渲染（可选，默认使用 NotebookDefaultCardList）
   *  返回 { stickySlot, content }，stickySlot 会被渲染为 sticky 定位的顶部栏，content 为条目列表 */
  renderEntryDisplay?: (props: {
    entries: Record<string, unknown>[];
    onEdit: (entry: Record<string, unknown>) => void;
    onDelete: (id: string) => void;
    selectedIds: Set<string>;
    onToggleSelect: (id: string) => void;
    onSelectAll: () => void;
    onDeselectAll: () => void;
  }) => { stickySlot?: React.ReactNode; content: React.ReactNode };
}

export const NotebookLayout: React.FC<NotebookLayoutProps> = ({
  notetype,
  emoji,
  renderEntryDisplay,
}) => {
  const navigate = useNavigate();
  const store = useNotebookStore();
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const toggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const handleSelectAll = useCallback(async () => {
    try {
      const res = await notebookApi.queryEntries(notetype, {
        filter: store.filterJson || undefined,
        page: 1,
        page_size: store.total,
        order_by: store.orderBy,
        order_dir: store.orderDir,
        columns: store.schema?.display_order || [],
      });
      setSelectedIds(new Set(res.entries.map((e: Record<string, unknown>) => e.id as string)));
    } catch {
      // 获取所有 ID 失败时静默处理
    }
  }, [notetype, store.filterJson, store.total, store.orderBy, store.orderDir]);

  const handleDeselectAll = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  const handleBatchDelete = useCallback(async () => {
    const ids = Array.from(selectedIds);
    if (ids.length === 0) return;
    if (confirm(`确定删除 ${ids.length} 条${TYPE_LABELS[notetype]}？`)) {
      await store.deleteEntries(ids);
      setSelectedIds(new Set());
    }
  }, [selectedIds, store, notetype]);

  const handleBatchUpdate = useCallback(() => {
    const ids = Array.from(selectedIds);
    if (ids.length === 0) return;
    navigate(`/notebooks/${notetype}/batch-update`, { state: { ids } });
  }, [selectedIds, navigate, notetype]);

  useEffect(() => {
    store.setCurrentType(notetype);
  }, [notetype]);

  const handleSubmit = useCallback(
    async (data: Record<string, unknown>) => {
      await store.addEntries([data]);
    },
    [store],
  );

  const handleEdit = useCallback((entry: Record<string, unknown>) => {
    navigate(`/notebooks/${notetype}/edit/${entry.id}`);
  }, [navigate, notetype]);

  const handleDelete = useCallback(
    async (id: string) => {
      if (confirm('确定删除该条目？')) {
        await store.deleteEntries([id]);
      }
    },
    [store],
  );

  // 选中数量
  const selectedCount = selectedIds.size;

  const label = TYPE_LABELS[notetype];
  const icon = emoji || DEFAULT_EMOJIS[notetype];

  return (
    <div className="space-y-4 animate-fade-in">
      {/* 标题栏 — 筛选 / 新增 / 批量操作 三按钮并列 — sticky */}
      <div className="sticky top-0 z-10 flex items-center justify-between bg-background py-2">
        <h1 className="text-xl font-bold">{icon} {label}</h1>
        <div className="flex items-center gap-2">
          {selectedIds.size > 0 ? (
            <>
              <Button variant="destructive" size="sm" onClick={handleBatchDelete}>
                删除 {selectedCount} 项
              </Button>
              <Button variant="outline" size="sm" onClick={handleBatchUpdate}>
                批量更新
              </Button>
              <Button variant="outline" size="sm" onClick={handleDeselectAll}>
                全不选
              </Button>
            </>
          ) : (
            <Button variant="outline" size="sm" onClick={handleSelectAll}>
              全选
            </Button>
          )}
          <Button variant="outline" onClick={() => navigate(`/notebooks/${notetype}/filter`)}>
            筛选
          </Button>
          <Button onClick={() => navigate(`/notebooks/${notetype}/new`)}>
            + 添加条目
          </Button>
        </div>
      </div>

      {/* 加载/错误 */}
      {store.error && (
        <div className="text-sm text-destructive bg-destructive/10 p-2 rounded">
          {store.error}
          <button onClick={store.clearError} className="ml-2 underline">关闭</button>
        </div>
      )}

      {/* 加载中 — 隐藏旧内容，只显示加载状态 */}
      {store.loading ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          加载中...
        </div>
      ) : store.entries.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground text-sm">
          暂无条目
        </div>
      ) : (
        (() => {
          const rendered = renderEntryDisplay
            ? renderEntryDisplay({ entries: store.entries, onEdit: handleEdit, onDelete: handleDelete, selectedIds, onToggleSelect: toggleSelect, onSelectAll: handleSelectAll, onDeselectAll: handleDeselectAll })
            : defaultRenderEntryDisplay({
                type: notetype,
                entries: store.entries,
                onEdit: handleEdit,
                onDelete: handleDelete,
                selectedIds,
                onToggleSelect: toggleSelect,
                page: store.page,
                pageSize: store.pageSize,
                total: store.total,
                onPageChange: store.setPage,
                onPageSizeChange: store.setPageSize,
              });

          const { stickySlot, content } = rendered;
          return (
            <>
              {stickySlot && (
                <div className="sticky top-12 z-10 bg-background py-2 border-b">
                  {stickySlot}
                </div>
              )}
              {content}
            </>
          );
        })()
      )}
    </div>
  );
};
