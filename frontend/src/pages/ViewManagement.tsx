import React, { useEffect, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import * as viewsApi from '@/api/views';
import type { ViewFile, ViewData } from '@/types/view';

export const ViewManagement: React.FC = () => {
  const [viewFiles, setViewFiles] = useState<ViewFile[]>([]);
  const [selectedView, setSelectedView] = useState<string | null>(null);
  const [viewContent, setViewContent] = useState('');
  const [newViewName, setNewViewName] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const loadViews = useCallback(async () => {
    try {
      const res = await viewsApi.listViews();
      setViewFiles(res || []);
    } catch (e: any) {
      setMessage(`加载失败: ${e.message}`);
    }
  }, []);

  useEffect(() => {
    loadViews();
  }, [loadViews]);

  const loadViewContent = async (name: string) => {
    try {
      setLoading(true);
      const data = await viewsApi.getView(name);
      setSelectedView(name);
      setViewContent(JSON.stringify(data, null, 2));
      setMessage('');
    } catch (e: any) {
      setMessage(`加载视图失败: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const saveView = async () => {
    if (!selectedView) return;
    try {
      setLoading(true);
      const parsed = JSON.parse(viewContent);
      await viewsApi.saveView(selectedView, parsed);
      setMessage('保存成功');
      loadViews();
    } catch (e: any) {
      setMessage(e instanceof SyntaxError ? 'JSON 格式错误' : `保存失败: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const createView = async () => {
    const name = newViewName.trim();
    if (!name) return;
    const defaultView: ViewData = {
      name,
      tables: [],
      label: name,
      description: '',
      version: 1,
    };
    try {
      setLoading(true);
      await viewsApi.saveView(name, defaultView);
      setNewViewName('');
      setMessage(`视图 "${name}" 已创建`);
      loadViews();
    } catch (e: any) {
      setMessage(`创建失败: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const deleteView = async (name: string) => {
    if (!confirm(`确定删除视图 "${name}"？`)) return;
    try {
      await viewsApi.deleteView(name);
      if (selectedView === name) {
        setSelectedView(null);
        setViewContent('');
      }
      setMessage('已删除');
      loadViews();
    } catch (e: any) {
      setMessage(`删除失败: ${e.message}`);
    }
  };

  return (
    <div className="space-y-4 animate-fade-in">
      <h1 className="text-xl font-bold">👁️ 视图管理</h1>

      {message && (
        <div className="text-sm px-3 py-2 rounded bg-secondary text-secondary-foreground">
          {message}
          <button onClick={() => setMessage('')} className="ml-2 underline">关闭</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* 视图文件列表 */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">视图文件</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {/* 新建 */}
            <div className="flex gap-2">
              <input
                value={newViewName}
                onChange={(e) => setNewViewName(e.target.value)}
                placeholder="新视图名称"
                className="flex-1 h-8 px-2 text-sm border rounded"
              />
              <Button size="sm" onClick={createView} disabled={loading}>
                创建
              </Button>
            </div>

            {/* 列表 */}
            <div className="space-y-1 max-h-80 overflow-y-auto">
              {viewFiles.length === 0 && (
                <p className="text-xs text-muted-foreground">暂无视图文件</p>
              )}
              {viewFiles.map((vf) => (
                <div
                  key={vf.name}
                  className={`flex items-center justify-between px-2 py-1.5 rounded cursor-pointer text-sm hover:bg-accent ${
                    selectedView === vf.name ? 'bg-accent' : ''
                  }`}
                  onClick={() => loadViewContent(vf.name)}
                >
                  <span className="truncate">{vf.name}</span>
                  <button
                    className="text-xs text-destructive hover:underline shrink-0 ml-2"
                    onClick={(e) => { e.stopPropagation(); deleteView(vf.name); }}
                  >
                    删除
                  </button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 编辑器 */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">
              {selectedView ? `编辑: ${selectedView}` : '选择视图'}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {selectedView ? (
              <>
                <Textarea
                  value={viewContent}
                  onChange={(e) => setViewContent(e.target.value)}
                  rows={20}
                  className="font-mono text-xs"
                />
                <div className="flex gap-2 justify-end">
                  <Button variant="outline" onClick={() => loadViewContent(selectedView)}>
                    重置
                  </Button>
                  <Button onClick={saveView} disabled={loading}>
                    保存
                  </Button>
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">
                从左侧选择一个视图文件进行编辑
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
