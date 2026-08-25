import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { NotebookForm } from '@/components/notebook/NotebookForm';
import { useNotebookStore, useCurrentNotebookData } from '@/stores/notebookStore';
import { handleError } from '@/lib/error';
import { NOTEBOOK_INFO, type NotebookType } from '@/config/notebook';
import { queryEntries } from '@/api/notebooks';
import type { Entry } from '@/types/notebook';

export type PageMode = 'create' | 'edit' | 'batch-update';

export const NotebookEditPage: React.FC = () => {
  const { notetype, id } = useParams<{ notetype: string; id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const store = useNotebookStore();
  const userData = useCurrentNotebookData();
  const [entry, setEntry] = useState<Entry | null>(null);
  const [loading, setLoading] = useState(true);

  const type = notetype as NotebookType;
  const label = NOTEBOOK_INFO[type].label || type;

  const mode: PageMode = location.pathname.endsWith('/batch-update')
    ? 'batch-update'
    : id
      ? 'edit'
      : 'create';

  const state = location.state as { ids?: string[] } | null;
  const batchIds: string[] = state?.ids ?? [];

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
        if (!userData || userData.type !== type) {
          await store.setCurrentType(type);
        }
        if (mode === 'edit' && id) {
          let found = userData?.entries?.find(e => e['id'] === id) as Entry | undefined;
          if (!found) {
            const res = await queryEntries(type, {
              limit: 1,
              filter: { col: 'id', op: '=', val: id },
            });
            found = res.results[0] || undefined;
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
        navigate(`/notebooks/${type}`, { replace: true });
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [type, mode, id, userData, store, label, navigate]);

  const handleSubmit = async (data: Entry) => {
    if (mode === 'batch-update') {
      const nonEmptyValues: Entry = {};
      for (const [key, value] of Object.entries(data)) {
        if (value !== '' && value !== null && value !== undefined) {
          nonEmptyValues[key] = value;
        }
      }
      if (Object.keys(nonEmptyValues).length !== 0) {
        await store.updateEntry(batchIds, nonEmptyValues);
      }
    } else if (mode === 'edit') {
      await store.updateEntry([id!], data);
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

  const schema = userData?.schema;

  return (
    <div className="space-y-4 animate-fade-in">
      {schema && (
        <NotebookForm
          schema={schema}
          initialData={mode === 'edit' ? entry || null : null}
          onSubmit={handleSubmit}
          onCancel={() => navigate(`/notebooks/${type}`, { state: { returnIds: batchIds } })}
          title={mode === 'edit' ? `编辑${label}` : mode === 'batch-update' ? `批量更新 ${batchIds.length} 条${label}` : `新建${label}`}
          disableRequired={mode === 'batch-update'}
        />
      )}
    </div>
  );
};
