import React, { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { defaultRenderEntryDisplay } from '@/components/notebook/notebookCards/NotebookCardList';
import { PlusIcon, FilterIcon, BatchEditIcon, DeleteIcon, SelectAllIcon, DeselectAllIcon, ChevronUpIcon } from '@/components/ui/icons';
import { useNotebookStore } from '@/stores/notebookStore';
import * as notebookApi from '@/api/notebooks';
import { TYPE_LABELS } from '@/config/notebook';
import type { NotebookType } from '@/config/notebook';
import { useSidebarStore } from '@/stores/sidebarStore';

interface NotebookLayoutProps {
  /** 笔记本类型标识 */
  notetype: NotebookType;
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
  renderEntryDisplay,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const store = useNotebookStore();
  const { isCollapsed, toggleCollapsed } = useSidebarStore();
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [showTopButton, setShowTopButton] = useState(false);

  // 从路由 state 恢复选中 ID（批量更新取消返回时）
  useEffect(() => {
    const state = location.state as { returnIds?: string[] } | null;
    if (state?.returnIds && state.returnIds.length > 0) {
      setSelectedIds(new Set(state.returnIds));
      // 清除 state，避免刷新或后续导航时重复恢复
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location.state, navigate, location.pathname]);

  // 监听滚动容器，控制"回到顶部"按钮显示
  useEffect(() => {
    const container = document.getElementById('main-scroll-container');
    if (!container) return;

    const onScroll = () => {
      setShowTopButton(container.scrollTop > 20);
    };

    onScroll(); // 初始检查
    container.addEventListener('scroll', onScroll);
    return () => container.removeEventListener('scroll', onScroll);
  }, []);

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
        offset: 0,
        limit: store.total,
        order_by: store.orderBy,
        order_dir: store.orderDir,
        columns: store.schema?.display_order || [],
      });
      setSelectedIds(new Set(res.entries.map((e: Record<string, unknown>) => e.id as string)));
    } catch {
      // 获取所有 ID 失败时静默处理
    }
  }, [notetype, store.filterJson, store.total, store.orderBy, store.orderDir, store.schema?.display_order]);

  const handleDeselectAll = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  const confirmDeleteRef = useRef<string[]>([]);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);

  const handleBatchDelete = useCallback(() => {
    const ids = Array.from(selectedIds);
    if (ids.length === 0) return;
    confirmDeleteRef.current = ids;
    setConfirmDeleteOpen(true);
  }, [selectedIds]);

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

  const handleDelete = useCallback((id: string) => {
    confirmDeleteRef.current = [id];
    setConfirmDeleteOpen(true);
  }, []);

  const executeDelete = useCallback(async () => {
    const ids = confirmDeleteRef.current;
    if (ids.length === 0) return;
    await store.deleteEntries(ids);
    setSelectedIds(new Set());
    confirmDeleteRef.current = [];
  }, [store]);

  // 选中数量
  const selectedCount = selectedIds.size;

  const entryList = useMemo(() => {
    if (store.loading || store.entries.length === 0) return null;
    const rendered = renderEntryDisplay
      ? renderEntryDisplay({ entries: store.entries, onEdit: handleEdit, onDelete: handleDelete, selectedIds, onToggleSelect: toggleSelect, onSelectAll: handleSelectAll, onDeselectAll: handleDeselectAll })
      : defaultRenderEntryDisplay({
          type: notetype,
          entries: store.entries,
          selectedIds,
          onToggleSelect: toggleSelect,
          offset: store.offset,
          limit: store.limit,
          total: store.total,
          onOffsetChange: store.setOffset,
          onLimitChange: store.setLimit,
        });

    const { stickySlot, content } = rendered;
    return (
      <>
        {stickySlot && (
          <div className="sticky top-12 z-10 bg-background py-2 border-b -mx-6 px-6">
            {stickySlot}
          </div>
        )}
        {content}
      </>
    );
  }, [renderEntryDisplay, store.entries, store.offset, store.limit, store.total, notetype, selectedIds, toggleSelect, handleSelectAll, handleDeselectAll]);

  const label = TYPE_LABELS[notetype];

  return (
    <div className="space-y-4 animate-fade-in">
      {/* 标题栏 — 筛选 / 新增 / 批量操作 三按钮并列 — sticky */}
      <div className="sticky top-0 z-10 flex items-center justify-between bg-background py-2">
        <div className="flex items-center gap-2">
          <h1
            className="text-xl font-bold cursor-pointer select-none"
            onClick={() => { if (isCollapsed) toggleCollapsed(); }}
          >
            {label}
          </h1>
          {showTopButton && (
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                document.getElementById('main-scroll-container')?.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              title="滚动到顶部"
            >
              <ChevronUpIcon size={16}/>
            </Button>
          )}
        </div>
        <div className="flex items-center gap-2">
          {selectedIds.size > 0 ? (
            <>
              <Button variant="outline" size="sm" onClick={handleDeselectAll} title="取消全选">
                <DeselectAllIcon className='mr-1'/> {selectedCount}
              </Button>
              <Button variant="outline" size="sm" onClick={handleBatchUpdate} title="批量编辑">
                <BatchEditIcon/>
              </Button>
              <Button variant="destructive" size="sm" onClick={handleBatchDelete} title="批量删除">
                <DeleteIcon/>
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" size="sm" onClick={handleSelectAll} title="全选">
                <SelectAllIcon/>
              </Button>
              <Button variant="outline" onClick={() => navigate(`/notebooks/${notetype}/filter`)} size="sm" title="筛选">
                <FilterIcon/>
              </Button>
              <Button onClick={() => navigate(`/notebooks/${notetype}/new`)} size="sm" title="新增">
                <PlusIcon />
              </Button>
            </>
          )}

        </div>
      </div>

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
        entryList
      )}

      <ConfirmDialog
        open={confirmDeleteOpen}
        onOpenChange={setConfirmDeleteOpen}
        title={`删除${label}`}
        description={confirmDeleteRef.current.length === 1
          ? `确定删除该${label}？此操作不可撤销。`
          : `确定删除 ${confirmDeleteRef.current.length} 条${label}？此操作不可撤销。`
        }
        confirmText="删除"
        variant="destructive"
        onConfirm={executeDelete}
      />
    </div>
  );
};
