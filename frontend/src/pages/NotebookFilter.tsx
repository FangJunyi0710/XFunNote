import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { FilterEditor } from '@/components/notebook/FilterEditor';
import { cn } from '@/lib/utils';
import { useNotebookStore, useCurrentNotebookData } from '@/stores/notebookStore';
import { TYPE_LABELS } from '@/config/notebook';
import { FilterIcon, ReplyIcon, SubmitIcon } from '@/components/ui/icons';
import type { NotebookType } from '@/config/notebook';
import * as filterApi from '@/api/filters';
import type { FilterFile } from '@/api/filters';
import { handleError } from '@/lib/error';

export const NotebookFilter: React.FC = () => {
  const { notetype } = useParams<{ notetype: string }>();
  const navigate = useNavigate();
  const store = useNotebookStore();
  const userData = useCurrentNotebookData();
  const type = notetype as NotebookType;

  const [savedFilters, setSavedFilters] = useState<FilterFile[]>([]);
  const [selectedFilterName, setSelectedFilterName] = useState<string | null>(null);
  const [saveName, setSaveName] = useState('');
  const [currentFilter, setCurrentFilter] = useState<string | null>(null);

  useEffect(() => {
    if (type && userData?.currentType !== type) {
      store.setCurrentType(type);
    }
  }, [type, userData, store]);

  useEffect(() => {
    filterApi.listFilters().then(setSavedFilters).catch(() => {});
  }, []);

  const columns =
    userData?.schema?.columns.map((c) => ({ name: c.name, type: c.type })) || [];

  const handleApply = (filterJson: string | null) => {
    store.setFilter(filterJson);
    navigate(`/notebooks/${type}`);
  };

  const handleSave = async () => {
    if (!saveName.trim()) return;
    try {
      await filterApi.saveFilter(saveName.trim(), { data: currentFilter });
      setSaveName('');
      const list = await filterApi.listFilters();
      setSavedFilters(list);
    } catch (e: unknown) {
      handleError(e, '保存 filter 失败');
    }
  };

  const handleLoad = async (name: string) => {
    try {
      const data = await filterApi.getFilter(name);
      setCurrentFilter((data.data as string | undefined) ?? null);
      setSelectedFilterName(name);
    } catch (e: unknown) {
      handleError(e, '加载 filter 失败');
    }
  };

  const handleDelete = async (name: string) => {
    try {
      await filterApi.deleteFilter(name);
      setSavedFilters((prev) => prev.filter((f) => f.name !== name));
      if (selectedFilterName === name) {
        setSelectedFilterName(null);
        setCurrentFilter(null);
      }
    } catch (e: unknown) {
      handleError(e, '删除 filter 失败');
    }
  };

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold"><FilterIcon className="inline-block align-middle" /> 筛选{TYPE_LABELS[type] || ''}</h1>
        <Button variant="outline" onClick={() => navigate(`/notebooks/${type}`)} title="返回">
          <ReplyIcon />
        </Button>
      </div>

      {savedFilters.length > 0 && (
        <Card className="mb-4">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">已保存的筛选</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {savedFilters.map((f) => (
                <div
                  key={f.id}
                  className={cn(
                    'flex items-center gap-1 rounded-md border px-2 py-1 text-xs',
                    selectedFilterName === f.name
                      ? 'border-primary bg-primary/10'
                      : 'border-input',
                  )}
                >
                  <button
                    className="hover:underline"
                    onClick={() => handleLoad(f.name)}
                  >
                    {f.name}
                  </button>
                  <button
                    className="text-destructive hover:text-destructive/80 ml-1"
                    onClick={() => handleDelete(f.name)}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <FilterEditor
        columns={columns}
        initialFilter={currentFilter}
        onApply={handleApply}
        onChange={(json) => setCurrentFilter(json)}
      />

      <div className="flex items-center gap-2">
        <Input
          value={saveName}
          onChange={(e) => setSaveName(e.target.value)}
          placeholder="保存为命名筛选..."
          className="max-w-xs"
        />
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            if (saveName.trim()) {
              handleSave();
            }
          }}
          disabled={!saveName.trim()}
          title="保存筛选"
        >
          <SubmitIcon/>
        </Button>
      </div>
    </div>
  );
};
