import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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

export const NotebookEditPage: React.FC = () => {
  const { notetype, id } = useParams<{ notetype: string; id: string }>();
  const navigate = useNavigate();
  const store = useNotebookStore();
  const [entry, setEntry] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const type = notetype as NotebookType;
  const label = TYPE_LABELS[type] || type;
  const isEdit = !!id;

  useEffect(() => {
    if (!type) return;
    const load = async () => {
      try {
        setLoading(true);
        // 确保 schema 已加载
        if (!store.schema || store.currentType !== type) {
          await store.setCurrentType(type);
        }
        if (id) {
          // 编辑模式：加载条目数据
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
          // 新建模式：不需要加载条目
          setEntry({});
        }
      } catch (e: any) {
        setError(e.message || '加载失败');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [type, id]);

  const handleSubmit = async (data: Record<string, any>) => {
    if (isEdit) {
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

  if (error || (isEdit && !entry)) {
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
          initialData={isEdit ? entry || undefined : undefined}
          onSubmit={handleSubmit}
          onCancel={() => navigate(`/notebooks/${type}`)}
          title={isEdit ? `编辑${label}` : `新建${label}`}
        />
      )}
    </div>
  );
};
