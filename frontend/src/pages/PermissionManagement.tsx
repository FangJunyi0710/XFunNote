import React, { useEffect, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import * as permissionsApi from '@/api/permissions';
import type { Permission } from '@/types/permission';
import { handleError, handleSuccess } from '@/lib/error';

const EMPTY_FORM = {
  id: '',
  name: '',
  description: '',
  read_view: '',
  write_view: '',
};

export const PermissionManagement: React.FC = () => {
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [isCreating, setIsCreating] = useState(false);
  const [loading, setLoading] = useState(false);

  const loadPermissions = useCallback(async () => {
    try {
      const res = await permissionsApi.listPermissions();
      setPermissions(res || []);
    } catch (e: unknown) {
      handleError(e, '加载失败');
    }
  }, []);

  useEffect(() => {
    loadPermissions();
  }, [loadPermissions]);

  const selectPermission = async (id: string) => {
    try {
      setLoading(true);
      const p = await permissionsApi.getPermission(id);
      setSelectedId(p.id);
      setIsCreating(false);
      setForm({
        id: p.id,
        name: p.name,
        description: p.description || '',
        read_view: p.read_view,
        write_view: p.write_view,
      });
    } catch (e: unknown) {
      handleError(e, '加载失败');
    } finally {
      setLoading(false);
    }
  };

  const handleNew = () => {
    setSelectedId(null);
    setIsCreating(true);
    setForm(EMPTY_FORM);
  };

  const handleSave = async () => {
    if (!form.id.trim() || !form.name.trim()) {
      handleError(new Error('ID 和名称不能为空'), '保存失败');
      return;
    }
    let readViewObj: Record<string, any>;
    let writeViewObj: Record<string, any>;
    try {
      readViewObj = form.read_view ? JSON.parse(form.read_view) : {};
      writeViewObj = form.write_view ? JSON.parse(form.write_view) : {};
    } catch {
      handleError(new Error('read_view 或 write_view 的 JSON 格式不正确'), '保存失败');
      return;
    }
    try {
      setLoading(true);
      if (isCreating) {
        await permissionsApi.createPermission({
          id: form.id.trim(),
          name: form.name.trim(),
          description: form.description.trim() || undefined,
          read_view: readViewObj,
          write_view: writeViewObj,
        });
        handleSuccess('创建成功');
      } else if (selectedId) {
        await permissionsApi.updatePermission(selectedId, {
          name: form.name.trim(),
          description: form.description.trim() || undefined,
          read_view: readViewObj,
          write_view: writeViewObj,
        });
        handleSuccess('保存成功');
      }
      setIsCreating(false);
      await loadPermissions();
    } catch (e: unknown) {
      handleError(e, '保存失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm(`确定删除权限 "${id}"？`)) return;
    try {
      await permissionsApi.deletePermission(id);
      if (selectedId === id) {
        setSelectedId(null);
        setIsCreating(false);
        setForm(EMPTY_FORM);
      }
      handleSuccess('已删除');
      await loadPermissions();
    } catch (e: unknown) {
      handleError(e, '删除失败');
    }
  };

  const handleCancel = () => {
    setSelectedId(null);
    setIsCreating(false);
    setForm(EMPTY_FORM);
  };

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* 权限列表 */}
        <Card className="lg:col-span-1">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">权限列表</CardTitle>
            <Button size="sm" onClick={handleNew}>新建</Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-1 max-h-96 overflow-y-auto">
              {permissions.length === 0 && (
                <p className="text-xs text-muted-foreground">暂无权限</p>
              )}
              {permissions.map((p) => (
                <div
                  key={p.id}
                  className={`flex items-center justify-between px-2 py-1.5 rounded cursor-pointer text-sm hover:bg-accent ${
                    selectedId === p.id ? 'bg-accent' : ''
                  }`}
                  onClick={() => selectPermission(p.id)}
                >
                  <div className="truncate flex-1">
                    <span className="font-medium">{p.name}</span>
                    <span className="text-xs text-muted-foreground ml-2">({p.id})</span>
                  </div>
                  <button
                    className="text-xs text-destructive hover:underline shrink-0 ml-2"
                    onClick={(e) => { e.stopPropagation(); handleDelete(p.id); }}
                  >
                    删除
                  </button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 编辑表单 */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">
              {isCreating ? '新建权限' : selectedId ? `编辑: ${form.name}` : '选择权限'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {(isCreating || selectedId) ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="pid">ID</Label>
                    <Input
                      id="pid"
                      value={form.id}
                      onChange={(e) => setForm({ ...form, id: e.target.value })}
                      placeholder="permission_id"
                      disabled={!isCreating}
                    />
                    {!isCreating && (
                      <p className="text-xs text-muted-foreground">创建后不可修改</p>
                    )}
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="pname">名称</Label>
                    <Input
                      id="pname"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      placeholder="权限名称"
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="pdesc">描述</Label>
                  <Input
                    id="pdesc"
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    placeholder="可选描述"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="pread">read_view (JSON)</Label>
                  <Textarea
                    id="pread"
                    value={form.read_view}
                    onChange={(e) => setForm({ ...form, read_view: e.target.value })}
                    rows={8}
                    className="font-mono text-xs"
                    placeholder='{"table_name": {"columns": ["col1", "col2"]}}'
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="pwrite">write_view (JSON)</Label>
                  <Textarea
                    id="pwrite"
                    value={form.write_view}
                    onChange={(e) => setForm({ ...form, write_view: e.target.value })}
                    rows={8}
                    className="font-mono text-xs"
                    placeholder='{"table_name": {"columns": ["col1", "col2"]}}'
                  />
                </div>

                <div className="flex gap-2 justify-end">
                  <Button variant="outline" onClick={handleCancel}>取消</Button>
                  <Button onClick={handleSave} disabled={loading}>
                    {loading ? '保存中...' : '保存'}
                  </Button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                从左侧选择一个权限，或点击"新建"创建
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
