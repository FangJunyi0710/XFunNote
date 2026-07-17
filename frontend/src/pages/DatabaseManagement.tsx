import React, { useState, useCallback, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Select, SelectItem } from '@/components/ui/select';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import * as managementApi from '@/api/management';
import { handleError, handleSuccess } from '@/lib/error';
import { CloseIcon, SubmitIcon } from '@/components/ui/icons';

export const DatabaseManagement: React.FC = () => {
  const [loading, setLoading] = useState<string | null>(null);
  const [restoreDialogOpen, setRestoreDialogOpen] = useState(false);
  const [backupFiles, setBackupFiles] = useState<string[]>([]);
  const [selectedBackup, setSelectedBackup] = useState<string>('');

  const [resetConfirmOpen, setResetConfirmOpen] = useState(false);
  const [restoreConfirmOpen, setRestoreConfirmOpen] = useState(false);
  const restoreBackupRef = useRef('');

  const handleBackup = async () => {
    setLoading('backup');
    try {
      const res = await managementApi.backupDb();
      handleSuccess(res.message);
    } catch (e: unknown) {
      handleError(e, '备份失败');
    } finally {
      setLoading(null);
    }
  };

  const executeReset = async () => {
    const confirm2 = prompt('请输入 "reset" 确认重置：');
    if (confirm2 !== 'reset') return;
    setLoading('reset');
    try {
      const res = await managementApi.resetDb();
      handleSuccess(res.message);
    } catch (e: unknown) {
      handleError(e, '重置失败');
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
        handleError(new Error('没有找到备份文件'), '还原');
      } else {
        setSelectedBackup(res.backups[0]);
        setRestoreDialogOpen(true);
      }
    } catch (e: unknown) {
      handleError(e, '获取备份列表失败');
    } finally {
      setLoading(null);
    }
  }, []);

  const handleRestore = useCallback(() => {
    if (!selectedBackup) return;
    restoreBackupRef.current = selectedBackup;
    setRestoreConfirmOpen(true);
  }, [selectedBackup]);

  const executeRestore = useCallback(async () => {
    const backup = restoreBackupRef.current;
    if (!backup) return;
    setRestoreDialogOpen(false);
    setLoading('restore');
    try {
      const res = await managementApi.restoreDb(backup);
      handleSuccess(res.message);
    } catch (e: unknown) {
      handleError(e, '还原失败');
    } finally {
      setLoading(null);
    }
  }, []);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
              onClick={() => setResetConfirmOpen(true)}
              disabled={loading === 'reset'}
              className="w-full"
            >
              {loading === 'reset' ? '执行中...' : '重置数据库'}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* 选择备份文件对话框 */}
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
              <option value="" disabled>选择备份文件</option>
              {backupFiles.map((f) => (
                <SelectItem key={f} value={f}>
                  {f}
                </SelectItem>
              ))}
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRestoreDialogOpen(false)} title="取消">
              <CloseIcon/>
            </Button>
            <Button variant="destructive" onClick={handleRestore} disabled={!selectedBackup} title="还原">
              <SubmitIcon/>
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={resetConfirmOpen}
        onOpenChange={setResetConfirmOpen}
        title="重置数据库"
        description="确定要重置数据库？此操作将清空所有数据！确认后还需输入 &quot;reset&quot; 二次确认。"
        confirmText="继续"
        variant="destructive"
        onConfirm={executeReset}
      />
      <ConfirmDialog
        open={restoreConfirmOpen}
        onOpenChange={setRestoreConfirmOpen}
        title="还原数据库"
        description={`确定要从以下备份文件还原数据库？\n\n${restoreBackupRef.current}\n\n还原前会自动备份当前数据库。`}
        confirmText="还原"
        variant="destructive"
        onConfirm={executeRestore}
      />
    </div>
  );
};
