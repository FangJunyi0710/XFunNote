import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { FilterEditor } from '@/components/notebook/FilterEditor';
import { useNotebookStore, useCurrentNotebookData } from '@/stores/notebookStore';
import { TYPE_LABELS } from '@/config/notebook';
import { FilterIcon, ReplyIcon } from '@/components/ui/icons';
import type { NotebookType } from '@/config/notebook';

export const NotebookFilter: React.FC = () => {
  const { notetype } = useParams<{ notetype: string }>();
  const navigate = useNavigate();
  const store = useNotebookStore();
  const userData = useCurrentNotebookData();
  const type = notetype as NotebookType;

  const [currentFilter, setCurrentFilter] = useState<string | null>(null);

  useEffect(() => {
    if (type && userData?.currentType !== type) {
      store.setCurrentType(type);
    }
  }, [type, userData, store]);

  const columns = userData?.schema?.columns ?? [];

  const handleApply = (filterJson: string | null) => {
    store.setFilter(filterJson);
    navigate(`/notebooks/${type}`);
  };

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold"><FilterIcon className="inline-block align-middle" /> 筛选{TYPE_LABELS[type] || ''}</h1>
        <Button variant="outline" onClick={() => navigate(`/notebooks/${type}`)} title="返回">
          <ReplyIcon />
        </Button>
      </div>
      <FilterEditor
        columns={columns}
        initialFilter={currentFilter}
        onApply={handleApply}
        onChange={(json) => setCurrentFilter(json)}
      />
    </div>
  );
};
