import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { NotebookForm } from '@/components/notebook/NotebookForm';
import { NotebookDefaultCardList } from '@/components/notebook/NotebookDefaultCardList';
import { useNotebookStore } from '@/stores/notebookStore';
import type { NotebookType } from '@/types/notebook';

interface NotebookLayoutProps {
  /** 笔记本类型标识 */
  notetype: NotebookType;
  /** 标题 emoji */
  emoji?: string;
  /** 批量操作按钮（在"筛选"之前显示） */
  batchActions?: React.ReactNode;
  /** 自定义条目展示渲染（可选，默认使用 NotebookDefaultCardList）
   *  返回 { stickySlot, content }，stickySlot 会被渲染为 sticky 定位的顶部栏，content 为条目列表 */
  renderEntryDisplay?: (props: {
    entries: Record<string, any>[];
    onEdit: (entry: Record<string, any>) => void;
    onDelete: (id: string) => void;
  }) => { stickySlot?: React.ReactNode; content: React.ReactNode };
}

const TYPE_LABELS: Record<NotebookType, string> = {
  plan: '计划',
  diary: '日记',
  word: '单词',
  accumulation: '积累',
  aimemory: 'AI 记忆',
  timeline: '时间线',
  schedule: '日程',
};

const DEFAULT_EMOJIS: Record<NotebookType, string> = {
  plan: '📋',
  diary: '📝',
  word: '📖',
  accumulation: '📚',
  aimemory: '🧠',
  timeline: '📅',
  schedule: '📋',
};

export const NotebookLayout: React.FC<NotebookLayoutProps> = ({
  notetype,
  emoji,
  batchActions,
  renderEntryDisplay,
}) => {
  const navigate = useNavigate();
  const store = useNotebookStore();
  const [showForm, setShowForm] = useState(false);
  const [editEntry, setEditEntry] = useState<Record<string, any> | null>(null);

  useEffect(() => {
    store.setCurrentType(notetype);
  }, [notetype]);

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

  const label = TYPE_LABELS[notetype];
  const icon = emoji || DEFAULT_EMOJIS[notetype];

  return (
    <div className="space-y-4 animate-fade-in">
      {/* 标题栏 — 筛选 / 新增 / 批量操作 三按钮并列 — sticky */}
      <div className="sticky top-0 z-10 flex items-center justify-between bg-background py-2">
        <h1 className="text-xl font-bold">{icon} {label}</h1>
        <div className="flex items-center gap-2">
          {batchActions}
          <Button variant="outline" onClick={() => navigate(`/notebooks/${notetype}/filter`)}>
            筛选
          </Button>
          <Button onClick={() => { setEditEntry(null); setShowForm(true); }}>
            + 添加条目
          </Button>
        </div>
      </div>

      {/* 表单 */}
      {showForm && store.schema && (
        <NotebookForm
          schema={store.schema}
          initialData={editEntry || undefined}
          onSubmit={handleSubmit}
          onCancel={() => { setShowForm(false); setEditEntry(null); }}
          title={editEntry ? `编辑${label}` : `新建${label}`}
        />
      )}

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
            ? renderEntryDisplay({ entries: store.entries, onEdit: handleEdit, onDelete: handleDelete })
            : null;

          if (rendered && 'content' in rendered) {
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
          }

          return rendered ?? (
            <NotebookDefaultCardList
              type={notetype}
              entries={store.entries}
              displayOrder={store.schema?.display_order || []}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          );
        })()
      )}
    </div>
  );
};
