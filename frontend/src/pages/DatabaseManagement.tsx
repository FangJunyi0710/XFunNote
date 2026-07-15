import React, { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import * as managementApi from '@/api/management';

export const DatabaseManagement: React.FC = () => {
  const [loading, setLoading] = useState<string | null>(null);
  const [log, setLog] = useState<{ time: string; msg: string; type: 'info' | 'error' | 'success' }[]>([]);
  const [restoreDialogOpen, setRestoreDialogOpen] = useState(false);
  const [backupFiles, setBackupFiles] = useState<string[]>([]);
  const [selectedBackup, setSelectedBackup] = useState<string>('');

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
      addLog(`备份成功: ${res.message}`, 'success');
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

  const openRestoreDialog = useCallback(async () => {
    setLoading('list');
    try {
      const res = await managementApi.listBackups();
      setBackupFiles(res.backups);
      if (res.backups.length === 0) {
        addLog('没有找到备份文件', 'info');
      } else {
        setSelectedBackup(res.backups[0]);
        setRestoreDialogOpen(true);
      }
    } catch (e: any) {
      addLog(`获取备份列表失败: ${e.message}`, 'error');
    } finally {
      setLoading(null);
    }
  }, []);

  const handleRestore = useCallback(async () => {
    if (!selectedBackup) return;
    if (!confirm(`⚠️ 确定要从以下备份文件还原数据库？\n\n${selectedBackup}\n\n还原前会自动备份当前数据库。`)) {
      return;
    }
    setRestoreDialogOpen(false);
    setLoading('restore');
    try {
      const res = await managementApi.restoreDb(selectedBackup);
      addLog(`还原成功: ${res.message}`, 'success');
    } catch (e: any) {
      addLog(`还原失败: ${e.message}`, 'error');
    } finally {
      setLoading(null);
    }
  }, [selectedBackup]);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
            <CardTitle className="text-base">还原</CardTitle>
            <CardDescription>从备份文件恢复数据</CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              variant="outline"
              onClick={openRestoreDialog}
              disabled={loading === 'list' || loading === 'restore'}
              className="w-full"
            >
              {loading === 'list' ? '查询中...' : loading === 'restore' ? '还原中...' : '从备份还原'}
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

      {/* 还原对话框 */}
      <Dialog open={restoreDialogOpen} onOpenChange={setRestoreDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>选择备份文件</DialogTitle>
            <DialogDescription>
              请选择要还原的备份文件。还原前会自动备份当前数据库。
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Select value={selectedBackup} onChange={(e) => setSelectedBackup(e.target.value)}>
              <SelectTrigger>
                <SelectValue>{selectedBackup || '选择备份文件'}</SelectValue>
              </SelectTrigger>
              <SelectContent>
                {backupFiles.map((f) => (
                  <SelectItem key={f} value={f}>
                    {f}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRestoreDialogOpen(false)}>
              取消
            </Button>
            <Button variant="destructive" onClick={handleRestore} disabled={!selectedBackup}>
              确认还原
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

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
                  ? 'text-success'
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
