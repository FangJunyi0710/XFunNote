import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { NotebookForm } from '@/components/notebook/notebookForms/defaultForm';
import { useNotebookStore } from '@/stores/notebookStore';
import * as notebookApi from '@/api/notebooks';
import { TYPE_LABELS } from '@/config/notebook';
import { handleError } from '@/lib/error';
import { ReplyIcon } from '@/components/ui/icons';
import type { NotebookType } from '@/config/notebook';

export type PageMode = 'create' | 'edit' | 'batch-update';

export const NotebookEditPage: React.FC = () => {
  const { notetype, id } = useParams<{ notetype: string; id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const store = useNotebookStore();
  const [entry, setEntry] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  const type = notetype as NotebookType;
  const label = TYPE_LABELS[type] || type;

  // 判断页面模式
  const mode: PageMode = location.pathname.endsWith('/batch-update')
    ? 'batch-update'
    : id
      ? 'edit'
      : 'create';

  // 批量更新时从路由 state 获取 ID 列表
  const state = location.state as { ids?: string[] } | null;
  const batchIds: string[] = state?.ids ?? [];

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
          let found = store.entries.find((e) => e.id === id) as Record<string, unknown> | undefined;
          if (!found) {
            const res = await notebookApi.queryEntries(type, {
              filter: JSON.stringify({ column: 'id', op: '=', value: id }),
              page: 1,
              page_size: 1,
              columns: [],
            });
            found = res.entries[0] || null;
          }
          if (!found) {
            handleError(new Error(`未找到该${label}条目`), '加载失败');
            navigate(`/notebooks/${type}`, { replace: true });
            return;
          }
          setEntry(found);
        } else {
          setEntry({});
        }
      } catch (e: unknown) {
        handleError(e, '加载失败');
        navigate(`/notebooks/${type}`);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [type, mode, id]);

  const handleSubmit = async (data: Record<string, unknown>) => {
    if (mode === 'batch-update') {
      // 过滤掉空值——空值表示不更新此字段
      const nonEmptyValues: Record<string, unknown> = {};
      for (const [key, value] of Object.entries(data)) {
        if (value !== '' && value !== null && value !== undefined) {
          nonEmptyValues[key] = value;
        }
      }
      if (Object.keys(nonEmptyValues).length !== 0) {
        await store.batchUpdateEntries(batchIds, nonEmptyValues);
      }
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

  if (mode === 'edit' && !entry && !loading) {
    return null;
  }

  return (
    <div className="space-y-4 animate-fade-in">
      {store.schema && (
        <NotebookForm
          schema={store.schema}
          initialData={mode === 'edit' ? entry || undefined : undefined}
          onSubmit={handleSubmit}
          onCancel={() => navigate(`/notebooks/${type}`, { state: { returnIds: batchIds } })}
          title={mode === 'edit' ? `编辑${label}` : mode === 'batch-update' ? `批量更新 ${batchIds.length} 条${label}` : `新建${label}`}
          disableRequired={mode === 'batch-update'}
        />
      )}
    </div>
  );
};
