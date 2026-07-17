import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { FilterEditor } from '@/components/notebook/FilterEditor';
import { cn } from '@/lib/utils';
import { useNotebookStore } from '@/stores/notebookStore';
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
  const type = notetype as NotebookType;

  // 命名 filter 管理
  const [savedFilters, setSavedFilters] = useState<FilterFile[]>([]);
  const [selectedFilterName, setSelectedFilterName] = useState<string | null>(null);
  const [saveName, setSaveName] = useState('');

  // 当前 filter DNF 字符串（用于回显编辑器）
  const [currentFilter, setCurrentFilter] = useState<string | null>(null);

  useEffect(() => {
    if (type && store.currentType !== type) {
      store.setCurrentType(type);
    }
  }, [type, store]);

  // 加载已保存的 filter
  useEffect(() => {
    filterApi.listFilters().then(setSavedFilters).catch(() => {});
  }, []);

  const columns =
    store.schema?.columns.map((c) => ({ name: c.name, type: c.type })) || [];

  // ── 应用 filter ──────────────────────────────────────────
  const handleApply = (filterJson: string | null) => {
    store.setFilter(filterJson);
    navigate(`/notebooks/${type}`);
  };

  // ── 保存命名 filter ──────────────────────────────────────
  const handleSave = async () => {
    if (!saveName.trim()) return;
    // 从编辑器获取当前 DNF —— 通过编辑器内部状态管理，这里使用已应用的 currentFilter
    // 实际上用户点击保存时，当前编辑器内容就是最新的
    try {
      await filterApi.saveFilter(saveName.trim(), { data: currentFilter });
      setSaveName('');
      // 刷新列表
      const list = await filterApi.listFilters();
      setSavedFilters(list);
    } catch (e: unknown) {
      handleError(e, '保存 filter 失败');
    }
  };

  // ── 加载命名 filter ──────────────────────────────────────
  const handleLoad = async (name: string) => {
    try {
      const data = await filterApi.getFilter(name);
      setCurrentFilter((data.data as string | undefined) ?? null);
      setSelectedFilterName(name);
    } catch (e: unknown) {
      handleError(e, '加载 filter 失败');
    }
  };

  // ── 删除命名 filter ──────────────────────────────────────
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
      {/* 顶部导航 */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold"><FilterIcon className="inline-block align-middle" /> 筛选{TYPE_LABELS[type] || ''}</h1>
        <Button variant="outline" onClick={() => navigate(`/notebooks/${type}`)} title="返回">
          <ReplyIcon />
        </Button>
      </div>

      {/* 已保存的 filter 列表 */}
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

      {/* Filter 编辑器 */}
      <FilterEditor
        columns={columns}
        initialFilter={currentFilter}
        onApply={handleApply}
        onChange={(json) => setCurrentFilter(json)}
      />

      {/* 保存命名 filter */}
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
