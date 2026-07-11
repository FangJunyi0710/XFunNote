import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import * as managementApi from '@/api/management';

export const Management: React.FC = () => {
  const [loading, setLoading] = useState<string | null>(null);
  const [log, setLog] = useState<{ time: string; msg: string; type: 'info' | 'error' | 'success' }[]>([]);

  const addLog = (msg: string, type: 'info' | 'error' | 'success' = 'info') => {
    setLog((prev) => [
      ...prev,
      { time: new Date().toLocaleTimeString(), msg, type },
    ]);
  };

  const handleInit = async () => {
    if (!confirm('确定要初始化数据库？这将创建缺失的表。')) return;
    setLoading('init');
    try {
      const res = await managementApi.initDb();
      addLog(`初始化成功: ${res.message}`, 'success');
    } catch (e: any) {
      addLog(`初始化失败: ${e.message}`, 'error');
    } finally {
      setLoading(null);
    }
  };

  const handleBackup = async () => {
    setLoading('backup');
    try {
      const res = await managementApi.backupDb();
      addLog(`备份成功: ${res.path}`, 'success');
    } catch (e: any) {
      addLog(`备份失败: ${e.message}`, 'error');
    } finally {
      setLoading(null);
    }
  };

  const handleReset = async () => {
    if (!confirm('⚠️ 确定要重置数据库？此操作将清空所有数据！\n\n确认后再次输入 "reset" 确认：')) {
      return;
    }
    const confirm2 = prompt('请输入 "reset" 确认重置：');
    if (confirm2 !== 'reset') {
      addLog('取消重置', 'info');
      return;
    }
    setLoading('reset');
    try {
      const res = await managementApi.resetDb();
      addLog(`重置成功: ${res.message}`, 'success');
    } catch (e: any) {
      addLog(`重置失败: ${e.message}`, 'error');
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="space-y-4 animate-fade-in">
      <h1 className="text-xl font-bold">⚙️ 数据库管理</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">初始化</CardTitle>
            <CardDescription>创建所有缺失的表结构</CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              onClick={handleInit}
              disabled={loading === 'init'}
              className="w-full"
            >
              {loading === 'init' ? '执行中...' : '初始化数据库'}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">备份</CardTitle>
            <CardDescription>备份当前数据库到文件</CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              variant="outline"
              onClick={handleBackup}
              disabled={loading === 'backup'}
              className="w-full"
            >
              {loading === 'backup' ? '执行中...' : '备份数据库'}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">重置</CardTitle>
            <CardDescription>清空所有数据（危险操作）</CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              variant="destructive"
              onClick={handleReset}
              disabled={loading === 'reset'}
              className="w-full"
            >
              {loading === 'reset' ? '执行中...' : '重置数据库'}
            </Button>
          </CardContent>
        </Card>
      </div>

      <Separator />

      {/* 操作日志 */}
      <div>
        <h2 className="text-sm font-semibold mb-2">操作日志</h2>
        <div className="bg-muted rounded-lg p-3 max-h-48 overflow-y-auto space-y-1">
          {log.length === 0 && (
            <p className="text-xs text-muted-foreground">暂无操作记录</p>
          )}
          {log.map((entry, i) => (
            <div
              key={i}
              className={`text-xs ${
                entry.type === 'error'
                  ? 'text-destructive'
                  : entry.type === 'success'
                  ? 'text-green-600'
                  : 'text-muted-foreground'
              }`}
            >
              [{entry.time}] {entry.msg}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
