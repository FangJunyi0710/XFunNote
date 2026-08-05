import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { FilterEditor, serializeFilter } from '@/components/notebook/FilterEditor';
import { useNotebookStore, useCurrentNotebookData } from '@/stores/notebookStore';
import { TYPE_LABELS } from '@/config/notebook';
import { FilterIcon, ReplyIcon, SubmitIcon } from '@/components/ui/icons';
import type { NotebookType } from '@/config/notebook';
import type { FilterState } from '@/types/filter';

export const NotebookFilter: React.FC = () => {
  const { notetype } = useParams<{ notetype: string }>();
  const navigate = useNavigate();
  const store = useNotebookStore();
  const userData = useCurrentNotebookData();
  const type = notetype as NotebookType;

  const [currentFilter, setCurrentFilter] = useState<FilterState>({filter: []});
  const [applying, setApplying] = useState<boolean>(false);

  useEffect(() => {
    if (type && userData?.currentType !== type) {
      store.setCurrentType(type);
    }
  }, [type, userData, store]);

  const columns = userData?.schema?.columns ?? [];

  const handleApply = async (e: React.FormEvent) => {
    e.preventDefault();
    setApplying(true);
    try {
      store.setFilter(serializeFilter(currentFilter));
      navigate(`/notebooks/${type}`);
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="space-y-4 animate-fade-in">
      <form onSubmit={handleApply}>
        <span className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold"><FilterIcon className="inline-block align-middle" /> 筛选{TYPE_LABELS[type] || ''}</h1>
          <span className="flex gap-2">
            <Button variant="outline" onClick={() => navigate(`/notebooks/${type}`)} title="返回">
              <ReplyIcon />
            </Button>
            <Button type="submit" disabled={applying} title="应用">
              <SubmitIcon />
            </Button>
          </span>
        </span>
        <FilterEditor
          columns={columns}
          value={currentFilter}
          onChange={state => setCurrentFilter(state ?? {filter: []})}
        />
      </form>
    </div>
  );
};
