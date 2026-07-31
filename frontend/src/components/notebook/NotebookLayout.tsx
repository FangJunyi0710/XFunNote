import React, { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { NotebookCard } from '@/components/notebook/NotebookCard';
import { Pagination } from '@/components/notebook/Pagination';
import { PlusIcon, FilterIcon, BatchEditIcon, DeleteIcon, SelectAllIcon, DeselectAllIcon, ChevronUpIcon } from '@/components/ui/icons';
import { useNotebookStore, useCurrentNotebookData } from '@/stores/notebookStore';
import * as notebookApi from '@/api/notebooks';
import { TYPE_LABELS } from '@/config/notebook';
import type { NotebookType } from '@/config/notebook';
import { useSidebarStore } from '@/stores/sidebarStore';
import { useTokenStore } from '@/stores/tokenStore';

interface NotebookLayoutProps {
  notetype: NotebookType;
}

export const NotebookLayout: React.FC<NotebookLayoutProps> = ({
  notetype
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const store = useNotebookStore();
  const userData = useCurrentNotebookData();
  const { isCollapsed, toggleCollapsed } = useSidebarStore();
  const activeUserName = useTokenStore((s) => s.activeUserName);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [showTopButton, setShowTopButton] = useState(false);
  const getStorageKey = (userName: string) => `xfun-selected-ids-${userName}-${notetype}`;

  useEffect(() => {
    const state = location.state as { returnIds?: string[] } | null;
    if (state?.returnIds && state.returnIds.length > 0) {
      setSelectedIds(new Set(state.returnIds));
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location.state, navigate, location.pathname]);

  // 从 sessionStorage 恢复选中状态
  useEffect(() => {
    if (!activeUserName) return;
    const key = getStorageKey(activeUserName);
    const stored = sessionStorage.getItem(key);
    if (stored) {
      try {
        const ids = JSON.parse(stored);
        if (Array.isArray(ids) && ids.length > 0) {
          setSelectedIds(new Set(ids));
        }
      } catch {
        // ignore
      }
    }
  }, [activeUserName]);

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

  // 选中状态变化时保存到 sessionStorage
  useEffect(() => {
    if (!activeUserName) return;
    const key = getStorageKey(activeUserName);
    const ids = Array.from(selectedIds);
    if (ids.length === 0) {
      sessionStorage.removeItem(key);
    } else {
      sessionStorage.setItem(key, JSON.stringify(ids));
    }
  }, [selectedIds, activeUserName]);

  const handleSelectAll = useCallback(async () => {
    try {
      const queryParams: Parameters<typeof notebookApi.queryEntries>[1] = {
        offset: 0,
        limit: userData?.total || 0,
        order_by: userData?.orderBy || 'id',
        order_dir: userData?.orderDir || 'desc',
        columns: userData?.schema?.display_order || [],
      };
      const filterJson = userData?.filterJson;
      if (filterJson !== null && filterJson !== undefined) {
        queryParams.filter = filterJson;
      }
      const res = await notebookApi.queryEntries(notetype, queryParams);
      setSelectedIds(new Set(res.entries.map((e: Record<string, unknown>) => e['id'] as string)));
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
    const { entries, offset, limit, total } = userData;
    return (
      <>
        <div className="sticky top-12 z-10 bg-background py-2 border-b -mx-6 px-6">
          {entries.length > 0 && offset !== undefined && store.setOffset ? (
            <Pagination
              offset={offset}
              limit={limit}
              total={total!}
              onOffsetChange={store.setOffset}
              onLimitChange={store.setLimit}
            />
          ) : undefined}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          {entries.map((entry) => (
            <NotebookCard
              key={entry['id'] as string}
              type={notetype}
              entry={entry}
              selected={selectedIds?.has(entry['id'] as string) || false}
              onSelect={toggleSelect}
            />
          ))}
        </div>
      </>
    );
  }, [userData, notetype, selectedIds, toggleSelect, store.loading, store.setOffset, store.setLimit]);

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
// TODO 前端增加卡片详情页
// TODO 前端添加标签编辑器、AI note等的移入移出等
// TODO 前端添加排序设置页面
// TODO 前端选择时应提供筛选出仅选择条目的视图便于更好呈现
// TODO 前端分各个本子做精致的数据呈现：点击本子进入仪表盘页面，再点击进入条目列表页面
