import React, { useEffect, useState, useCallback, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { TokenValueDisplay } from '@/components/ui/TokenValueDisplay';
import { CloseIcon, DeleteIcon, PlusIcon, SubmitIcon } from '@/components/ui/icons';
import * as tokensApi from '@/api/tokens';
import * as permissionsApi from '@/api/permissions';
import { handleError, handleSuccess } from '@/lib/error';
import type { Token } from '@/types/token';
import type { Permission } from '@/types/permission';

const EMPTY_FORM = {
  name: '',
  permission: '',
  is_active: true,
  expires_at: '',
  enable_shortcut: true,
  shortcut: '',
  shortcut_ttl: 120,
};

export const TokenManagement: React.FC = () => {
  const [tokens, setTokens] = useState<Token[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [isCreating, setIsCreating] = useState(false);
  const [loading, setLoading] = useState(false);

  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const pendingDeleteRef = useRef('');

  const loadData = useCallback(async () => {
    try {
      const [tokensRes, permsRes] = await Promise.all([
        tokensApi.listTokens(),
        permissionsApi.listPermissions(),
      ]);
      setTokens(tokensRes || []);
      setPermissions(permsRes || []);
    } catch (e: unknown) {
      handleError(e, '加载失败');
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const selectToken = async (id: string) => {
    try {
      setLoading(true);
      const t = await tokensApi.getToken(id);
      setSelectedId(t.id);
      setIsCreating(false);
      setForm({
        name: t.name,
        permission: t.permission,
        is_active: t.is_active === 1,
        expires_at: t.expires_at ? t.expires_at.slice(0, 16) : '',
        enable_shortcut: !!t.shortcut,
        shortcut: t.shortcut || '',
        shortcut_ttl: 120,
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
    setForm({
      name: '',
      permission: permissions.length > 0 ? permissions[0].uuid : '',
      is_active: true,
      expires_at: '',
      enable_shortcut: true,
      shortcut: '',
      shortcut_ttl: 120,
    });
  };

  const handleSave = async () => {
    if (!form.name.trim()) {
      handleError(new Error('名称不能为空'), '保存 Token');
      return;
    }
    if (!form.permission) {
      handleError(new Error('请选择权限'), '保存 Token');
      return;
    }
    try {
      setLoading(true);
      if (isCreating) {
        const created = await tokensApi.createToken({
          name: form.name.trim(),
          permission: form.permission,
          shortcut: form.enable_shortcut ? form.shortcut || undefined : undefined,
          shortcut_ttl: form.enable_shortcut ? form.shortcut_ttl : undefined,
        });
        handleSuccess('Token 创建成功');
        setIsCreating(false);
        setSelectedId(created.id);
      } else if (selectedId) {
        await tokensApi.updateToken(selectedId, {
          name: form.name.trim(),
          permission: form.permission,
          is_active: form.is_active,
          expires_at: form.expires_at || null,
        });
        handleSuccess('保存成功');
      }
      await loadData();
    } catch (e: unknown) {
      handleError(e, '保存失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = (id: string) => {
    pendingDeleteRef.current = id;
    setConfirmDeleteOpen(true);
  };

  const executeDelete = async () => {
    const id = pendingDeleteRef.current;
    if (!id) return;
    try {
      await tokensApi.deleteToken(id);
      if (selectedId === id) {
        setSelectedId(null);
        setIsCreating(false);
        setForm(EMPTY_FORM);
      }
      handleSuccess('已删除');
      await loadData();
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
        {/* Token 列表 */}
        <Card className="lg:col-span-1">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Token 列表</CardTitle>
            <Button size="sm" onClick={handleNew} title="新建 Token"><PlusIcon /></Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-1 max-h-96 overflow-y-auto">
              {tokens.length === 0 && (
                <p className="text-xs text-muted-foreground">暂无 Token</p>
              )}
              {tokens.map((t) => (
                <div
                  key={t.id}
                  className={`flex items-center justify-between px-2 py-1.5 rounded cursor-pointer text-sm hover:bg-accent ${
                    selectedId === t.id ? 'bg-accent' : ''
                  }`}
                  onClick={() => selectToken(t.id)}
                >
                  <div className="truncate flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="font-medium truncate">{t.name}</span>
                      <Badge variant={t.is_active ? 'success' : 'secondary'} className="shrink-0">
                        {t.is_active ? '启用' : '停用'}
                      </Badge>
                      {t.shortcut && (
                        <Badge variant="secondary" className="shrink-0 text-[10px]">
                          Shortcut
                        </Badge>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground truncate">
                      {t.permission}
                      {t.expires_at && ` | 过期: ${new Date(t.expires_at).toLocaleDateString()}`}
                      {t.shortcut && ` | 短码: ${t.shortcut}`}
                    </div>
                  </div>
                  <button
                    className="text-xs text-destructive hover:underline shrink-0 ml-2"
                    onClick={(e) => { e.stopPropagation(); handleDelete(t.id); }}
                    title="删除"
                  >
                    <DeleteIcon/>
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
              {isCreating ? '新建 Token' : selectedId ? `编辑: ${form.name}` : '选择 Token'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {(isCreating || selectedId) ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="tname">名称</Label>
                    <Input
                      id="tname"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      placeholder="Token 名称"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="tperm">权限</Label>
                    <Select
                      id="tperm"
                      value={form.permission}
                      onChange={(e) => setForm({ ...form, permission: e.target.value })}
                    >
                      {permissions.length === 0 && (
                        <option value="">暂无权限，请先创建</option>
                      )}
                      {permissions.map((p) => (
                        <option key={p.id} value={p.uuid}>
                          {p.name} ({p.uuid})
                        </option>
                      ))}
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label>启用</Label>
                    <div className="flex items-center gap-2 pt-1">
                      <Switch
                        checked={form.is_active}
                        onCheckedChange={(v) => setForm({ ...form, is_active: v })}
                      />
                      <span className="text-sm text-muted-foreground">
                        {form.is_active ? '已启用' : '已停用'}
                      </span>
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="texp">过期时间</Label>
                    <Input
                      id="texp"
                      type="datetime-local"
                      value={form.expires_at}
                      onChange={(e) => setForm({ ...form, expires_at: e.target.value })}
                    />
                    <p className="text-xs text-muted-foreground">留空表示永不过期</p>
                  </div>
                </div>

                {/* Shortcut 兑换码配置 */}
                <div className="space-y-3 border-t pt-3">
                  <div className="flex items-center justify-between">
                    <Label className="font-medium">Shortcut 兑换码</Label>
                    <Switch
                      checked={form.enable_shortcut}
                      onCheckedChange={(v) => setForm({ ...form, enable_shortcut: v })}
                    />
                  </div>
                  {form.enable_shortcut && (
                    <div className="grid grid-cols-2 gap-4 pl-2 border-l-2 border-primary/30">
                      <div className="space-y-1.5">
                        <Label htmlFor="tshortcut">自定义短码</Label>
                        <Input
                          id="tshortcut"
                          value={form.shortcut}
                          onChange={(e) => setForm({ ...form, shortcut: e.target.value })}
                          placeholder="自定义短码"
                        />
                      </div>
                      <div className="space-y-1.5">
                        <Label htmlFor="tshortcut_ttl">短码有效期（秒）</Label>
                        <Input
                          id="tshortcut_ttl"
                          type="number"
                          min={10}
                          max={86400}
                          value={form.shortcut_ttl}
                          onChange={(e) => setForm({ ...form, shortcut_ttl: parseInt(e.target.value) || 120 })}
                        />
                        <p className="text-xs text-muted-foreground">范围 10~86400 秒，默认 120 秒</p>
                      </div>
                    </div>
                  )}
                </div>

                {!isCreating && selectedId && (() => {
                  const t = tokens.find((tk) => tk.id === selectedId);
                  return t ? (
                    <div className="space-y-2">
                      <TokenValueDisplay
                        value={t.token}
                      />
                      {t.shortcut && (
                        <div className="space-y-1">
                          <Label>Shortcut 兑换码</Label>
                          <div className="flex items-center gap-2">
                            <code className="text-xs p-2 rounded bg-muted font-mono">
                              {t.shortcut}
                            </code>
                            {t.shortcut_expire_at && (
                              <span className="text-xs text-muted-foreground">
                                过期: {new Date(t.shortcut_expire_at).toLocaleString()}
                              </span>
                            )}
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={async () => {
                                try {
                                  await navigator.clipboard.writeText(t.shortcut!);
                                  handleSuccess('Shortcut 已复制到剪贴板');
                                } catch {
                                  handleError(new Error('复制失败'), '复制');
                                }
                              }}
                            >
                              复制短码
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : null;
                })()}

                <div className="flex gap-2 justify-end">
                  <Button variant="outline" onClick={handleCancel} title="取消"><CloseIcon/></Button>
                  <Button onClick={handleSave} disabled={loading} title="保存">
                    <SubmitIcon/>
                  </Button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                从左侧选择一个 Token，或点击"新建"创建
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <ConfirmDialog
        open={confirmDeleteOpen}
        onOpenChange={setConfirmDeleteOpen}
        title="删除 Token"
        description="确定删除此 Token？此操作不可撤销。"
        confirmText="删除"
        variant="destructive"
        onConfirm={executeDelete}
      />
    </div>
  );
};
