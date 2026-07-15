import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { FilterPanel } from '@/components/notebook/FilterPanel';
import { useNotebookStore } from '@/stores/notebookStore';
import { TYPE_LABELS } from '@/config/notebook';
import type { NotebookType } from '@/config/notebook';

export const NotebookFilter: React.FC = () => {
  const { notetype } = useParams<{ notetype: string }>();
  const navigate = useNavigate();
  const store = useNotebookStore();
  const type = notetype as NotebookType;

  useEffect(() => {
    if (type && store.currentType !== type) {
      store.setCurrentType(type);
    }
  }, [type, store]);

  const columns = store.schema?.columns.map((c) => ({ name: c.name, type: c.type })) || [];

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">🔍 筛选{TYPE_LABELS[type] || ''}</h1>
        <Button variant="outline" onClick={() => navigate(`/notebooks/${type}`)}>
          返回
        </Button>
      </div>
      <FilterPanel
        columns={columns}
        onApply={(filterJson) => {
          store.setFilter(filterJson);
          navigate(`/notebooks/${type}`);
        }}
      />
    </div>
  );
};
