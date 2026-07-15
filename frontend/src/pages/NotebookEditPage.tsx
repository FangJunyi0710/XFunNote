import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { NotebookForm } from '@/components/notebook/NotebookForm';
import { useNotebookStore } from '@/stores/notebookStore';
import * as notebookApi from '@/api/notebooks';
import type { NotebookType } from '@/types/notebook';

const TYPE_LABELS: Record<NotebookType, string> = {
  plan: '计划',
  diary: '日记',
  word: '单词',
  accumulation: '积累',
  aimemory: 'AI 记忆',
  timeline: '时间线',
  schedule: '日程',
};

export type PageMode = 'create' | 'edit' | 'batch-update';

export const NotebookEditPage: React.FC = () => {
  const { notetype, id } = useParams<{ notetype: string; id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const store = useNotebookStore();
  const [entry, setEntry] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const type = notetype as NotebookType;
  const label = TYPE_LABELS[type] || type;

  // 判断页面模式
  const mode: PageMode = location.pathname.endsWith('/batch-update')
    ? 'batch-update'
    : id
      ? 'edit'
      : 'create';

  // 批量更新时从路由 state 获取 ID 列表
  const batchIds: string[] = (location.state as any)?.ids ?? [];

  // 如果没有选中 ID，重定向回列表页
  useEffect(() => {
    if (mode === 'batch-update' && batchIds.length === 0) {
      navigate(`/notebooks/${type}`, { replace: true });
    }
  }, [mode, batchIds, type, navigate]);

  useEffect(() => {
    if (!type) return;
    const load = async () => {
      try {
        setLoading(true);
        if (!store.schema || store.currentType !== type) {
          await store.setCurrentType(type);
        }
        if (mode === 'edit' && id) {
          let found = store.entries.find((e: any) => e.id === id);
          if (!found) {
            const res = await notebookApi.queryEntries(type, {
              filter: JSON.stringify({ column: 'id', op: '=', value: id }),
              page: 1,
              page_size: 1,
            });
            found = res.entries[0] || null;
          }
          setEntry(found);
        } else {
          setEntry({});
        }
      } catch (e: any) {
        setError(e.message || '加载失败');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [type, mode, id]);

  const handleSubmit = async (data: Record<string, any>) => {
    if (mode === 'batch-update') {
      // 过滤掉空值——空值表示不更新此字段
      const nonEmptyValues: Record<string, any> = {};
      for (const [key, value] of Object.entries(data)) {
        if (value !== '' && value !== null && value !== undefined) {
          nonEmptyValues[key] = value;
        }
      }
      if (Object.keys(nonEmptyValues).length === 0) {
        // 所有字段都为空则直接返回，无需弹窗
        return;
      }
      await store.batchUpdateEntries(batchIds, nonEmptyValues);
    } else if (mode === 'edit') {
      await store.updateEntry(id!, data);
    } else {
      await store.addEntries([data]);
    }
    navigate(`/notebooks/${type}`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-muted-foreground">
        加载中...
      </div>
    );
  }

  if (error || (mode === 'edit' && !entry)) {
    return (
      <div className="space-y-4">
        <button
          className="text-sm text-primary hover:underline"
          onClick={() => navigate(`/notebooks/${type}`)}
        >
          ← 返回 {label}
        </button>
        <div className="text-sm text-destructive bg-destructive/10 p-2 rounded">
          {error || '未找到该条目'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-fade-in">
      <button
        className="text-sm text-primary hover:underline"
        onClick={() => navigate(`/notebooks/${type}`)}
      >
        ← 返回 {label}
      </button>
      {store.schema && (
        <NotebookForm
          schema={store.schema}
          initialData={mode === 'edit' ? entry || undefined : undefined}
          onSubmit={handleSubmit}
          onCancel={() => navigate(`/notebooks/${type}`)}
          title={mode === 'edit' ? `编辑${label}` : mode === 'batch-update' ? `批量更新 ${batchIds.length} 条${label}` : `新建${label}`}
          disableRequired={mode === 'batch-update'}
        />
      )}
    </div>
  );
};
