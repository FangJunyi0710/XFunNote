import React, { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { defaultRenderEntryDisplay } from '@/components/notebook/notebookCards/NotebookCardList';
import { PlusIcon, FilterIcon, BatchEditIcon, DeleteIcon, SelectAllIcon, DeselectAllIcon, ChevronUpIcon } from '@/components/ui/icons';
import { useNotebookStore, useCurrentNotebookData } from '@/stores/notebookStore';
import * as notebookApi from '@/api/notebooks';
import { TYPE_LABELS } from '@/config/notebook';
import type { NotebookType } from '@/config/notebook';
import { useSidebarStore } from '@/stores/sidebarStore';

interface NotebookLayoutProps {
  notetype: NotebookType;
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
  const userData = useCurrentNotebookData();
  const { isCollapsed, toggleCollapsed } = useSidebarStore();
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [showTopButton, setShowTopButton] = useState(false);

  useEffect(() => {
    const state = location.state as { returnIds?: string[] } | null;
    if (state?.returnIds && state.returnIds.length > 0) {
      setSelectedIds(new Set(state.returnIds));
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location.state, navigate, location.pathname]);

  useEffect(() => {
    const container = document.getElementById('main-scroll-container');
    if (!container) return;
    const onScroll = () => setShowTopButton(container.scrollTop > 20);
    onScroll();
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
        filter: userData?.filterJson || undefined,
        offset: 0,
        limit: userData?.total || 0,
        order_by: userData?.orderBy || 'id',
        order_dir: userData?.orderDir || 'desc',
        columns: userData?.schema?.display_order || [],
      });
      setSelectedIds(new Set(res.entries.map((e: Record<string, unknown>) => e.id as string)));
    } catch {
      // ignore
    }
  }, [notetype, userData]);

  const handleDeselectAll = useCallback(() => setSelectedIds(new Set()), []);

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

  const selectedCount = selectedIds.size;

  const entryList = useMemo(() => {
    if (store.loading || !userData || userData.entries.length === 0) return null;
    const rendered = renderEntryDisplay
      ? renderEntryDisplay({ entries: userData.entries, onEdit: handleEdit, onDelete: handleDelete, selectedIds, onToggleSelect: toggleSelect, onSelectAll: handleSelectAll, onDeselectAll: handleDeselectAll })
      : defaultRenderEntryDisplay({
          type: notetype,
          entries: userData.entries,
          selectedIds,
          onToggleSelect: toggleSelect,
          offset: userData.offset,
          limit: userData.limit,
          total: userData.total,
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
  }, [renderEntryDisplay, userData, notetype, selectedIds, toggleSelect, handleSelectAll, handleDeselectAll, handleEdit, handleDelete, store.loading, store.setOffset, store.setLimit]);

  const label = TYPE_LABELS[notetype];

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="sticky top-0 z-10 flex items-center justify-between bg-background py-2 -mx-6 px-6">
        <div className="flex items-center gap-2">
          <h1
            className="text-xl font-bold cursor-pointer select-none"
            onClick={() => { if (isCollapsed) toggleCollapsed(); else navigate('/'); }}
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

      {store.loading ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          加载中...
        </div>
      ) : !userData || userData.entries.length === 0 ? (
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
